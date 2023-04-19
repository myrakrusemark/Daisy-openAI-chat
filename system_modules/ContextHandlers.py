import logging
import datetime
import json
import sqlite3
import time
import threading
from sqlite3 import Error
import sqlite3
import yaml
import system_modules.Chat as cht
import re

class ConnectionPool:
	def __init__(self, db_path, max_connections=5):
		self.db_path = db_path
		self.max_connections = max_connections
		self.connections = {}
		self.lock = threading.Lock()


	def get_connection(self):
		thread_id = threading.get_ident()
		self.lock.acquire()
		try:
			if thread_id in self.connections:
				return self.connections[thread_id]
			elif len(self.connections) < self.max_connections:
				conn = sqlite3.connect(self.db_path)
				self.connections[thread_id] = conn
				return conn
			else:
				raise Exception("Connection pool exhausted")
		finally:
			self.lock.release()

	def put_connection(self, conn):
		thread_id = threading.get_ident()
		self.lock.acquire()
		try:
			if thread_id in self.connections:
				self.connections[thread_id] = None
			else:
				conn.close()
		finally:
			self.lock.release()


class ContextHandlers:
	description = "A class for handling and managing messages in the chatGPT context object"

	def __init__(self, db_path):
		self.chat = cht.Chat()

		#Get and set conversation_id from configs.yaml
		self.conversation_id = None
		with open("configs.yaml", "r") as f:
			configs = yaml.safe_load(f)
		if 'conversation_id' in configs:
			self.conversation_id = configs.get("conversation_id")
			print("Using conversation id from configs: " + str(self.conversation_id))


		self.db_path = db_path
		self.messages = []
		self.start_prompts = []
		self.connection_pool = ConnectionPool(db_path)

		self.load_context()

	def update_conversation_name_summary(self):
		# Get the name of the current conversation from the LLM
		logging.info("Updating conversation name and summary...")
		context = self.get_context_without_timestamp()
		prompt = """
		Please respond with a name, and summary for this conversation.
		1. The name should be a single word or short phrase, no more than 5 words."
		2. The summary should be a short description of the conversation, no more than 2 paragraphs.
		3. The output must follow the following JSON format: {"name": name, "summary": summary}
		"""
		context.append(self.single_message_context('system', prompt, False))
		response = self.chat.request(context)

		# Extract the JSON response from the string
		response_match = re.search(r"{.*}", response)
		if response_match:
			response_json = response_match.group(0)
		else:
			logging.error("Invalid response format while setting conversation name and summary")
			return

		# Convert the JSON response to an object
		try:
			response_obj = json.loads(response_json)
		except Exception as e:
			logging.error("Invalid JSON response while setting conversation name and summary: " + str(e))
			return

		# Update the name and summary of the current conversation in the database
		with self.connection_pool.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				'''UPDATE conversations SET name = ?, summary = ? WHERE id = ?''',
				(response_obj["name"], response_obj["summary"], self.conversation_id)
			)
			conn.commit()

		logging.info("Name and summary updated: " + response_obj["name"])

		return


	def load_context(self):
		self.messages = []
		self.create_conversations_table_if_not_exists()
		with self.connection_pool.get_connection() as conn:

			cursor = conn.cursor()

			#Get the conversation ID
			if not self.conversation_id:
				cursor.execute('''
				SELECT id FROM conversations ORDER BY id DESC LIMIT 1;
				''')
				row = cursor.fetchone()
				if row:
					self.conversation_id = str(row[0])
					logging.info("No conversation id found in configs.yaml, loading latest conversation: " + str(self.conversation_id))

			#If conversation still is not set, create a new conversation ID
			if not self.conversation_id:
				self.conversation_id = str(int(time.time()))
				logging.info("No conversation found, creating new conversation: " + str(self.conversation_id))

			print("Conversation id: " + str(self.conversation_id))


			#Get the messages from the conversation ID
			cursor.execute('''
				SELECT * FROM messages WHERE id = ?
			''', (self.conversation_id,))
			rows = cursor.fetchall()
			if rows:
				for row in rows:
					message = json.loads(row[1])
					self.messages.append(message)
				print("Loaded "+ str(len(rows)) + " messages from conversation id: " + str(self.conversation_id))


	def create_conversations_table_if_not_exists(self):
		with self.connection_pool.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				CREATE TABLE IF NOT EXISTS messages (
					id TEXT NOT NULL,
					message TEXT NOT NULL
				);
			''')
			cursor.execute('''
				CREATE TABLE IF NOT EXISTS conversations (
					id TEXT PRIMARY KEY,
					name TEXT NOT NULL,
					summary TEXT NOT NULL
				);
			''')

	def save_context(self):
		logging.info("Saving context: " + str(self.conversation_id))
		with self.connection_pool.get_connection() as conn:
			conn.execute('''
				PRAGMA foreign_keys=OFF;
			''')
			conn.execute('''
				BEGIN TRANSACTION;
			''')

			# Insert conversation information if it doesn't already exist
			rows = conn.execute('''
				SELECT COUNT(*) FROM conversations WHERE id = ?;
			''', (self.conversation_id,)).fetchone()[0]
			if rows == 0:
				conn.execute('''
					INSERT INTO conversations (id, name, summary)
					VALUES (?, ?, ?);
				''', (self.conversation_id, "generic name", "generic summary"))

			# Save messages
			conn.execute('''
				DELETE FROM messages WHERE id = ?;
			''', (self.conversation_id,))
			for message in self.messages:
				json_message = json.dumps(message)
				conn.execute('''
					INSERT INTO messages (id, message) VALUES (?, ?);
				''', (self.conversation_id, json_message,))
			conn.execute('''
				COMMIT;
			''')
			row_count = conn.execute('''
				SELECT COUNT(*) FROM messages WHERE id = ?;
			''', (self.conversation_id,)).fetchone()[0]
			logging.info(f"Inserted {row_count} rows for conversation {self.conversation_id}.")


	def get_context(self):
		context = []
		#Append start prompts to messages
		for start_prompt in self.start_prompts:
			context.append(start_prompt)

		for message in self.messages:
			context.append(message)
		return context


	def get_context_without_timestamp(self):
		messages_without_timestamp = []

		for message in self.get_context():
			message_without_timestamp = message.copy()
			del message_without_timestamp['timestamp']
			messages_without_timestamp.append(message_without_timestamp)
		return messages_without_timestamp


	def single_message_context(self, role, message, incl_timestamp=True):
		if incl_timestamp:
			now = datetime.datetime.now()
			timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
			return {'role': role, 'timestamp': timestamp, 'content': str(message)}
		else:
			return {'role': role, 'content': str(message)}
		
	def add_start_propmpt(self, role="system", message=""):
		start_prompt = self.single_message_context(role, message)
		self.start_prompts.append(start_prompt)

	def add_message_object(self, role, message):
		logging.debug("Adding " + role + " message to context")
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
		new_message = {'role': role, 'timestamp': timestamp, 'content': str(message)}
		self.messages.append(new_message)
		self.save_context()
		logging.debug(self.messages)

	def add_message_object_at_start(self, role, message):
		logging.debug("Appending " + role + " message at start of context")
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
		new_message = {'role': role, 'timestamp': timestamp, 'content': str(message)}
		self.messages.insert(0, new_message)
		self.save_context()
		logging.debug(self.messages)

	def remove_last_message_object(self):
		if self.messages:
			self.messages.pop()
			self.save_context()

	def get_last_message_object(self, user_type=None):
		if user_type:
			for message in reversed(self.messages):
				if message['role'] == user_type:
					return message
		else:
			if self.messages:
				return self.messages[-1]
		return False

	def replace_last_message_object(self, message, user_type=None):
		if user_type:
			for i in reversed(range(len(self.messages))):
				if self.messages[i]['role'] == user_type:
					self.messages[i]['content'] = message
					self.save_context()
					return
		elif message and self.messages:
			self.messages[-1]['content'] = message
			self.save_context()

	def delete_message_at_index(self, index):
		try:
			index = int(index)
			if index < len(self.messages) and index >= 0:
				self.messages.pop(index)
				self.save_context()
				return True
		except ValueError:
			pass
		return False

	def update_message_at_index(self, message, index):
		try:
			index = int(index)
			if index < len(self.messages) and index >= 0:
				self.messages[index]['content'] = message
				now = datetime.datetime.now()
				self.messages[index]['timestamp'] = now.strftime('%Y-%m-%d %H:%M:%S')
				self.save_context()
		except ValueError:
			pass
		return False
