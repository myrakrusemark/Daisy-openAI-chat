
import logging
import datetime as dt
from datetime import datetime
start_prompt_Daisy = "You are Daisy, a voice assistant based on chatGPT, a large language model trained by OpenAI. You speak in confident but concise responses, about two sentences long. You are having a real-world vocal conversation. Current date: " + datetime.now().strftime("%Y-%m-%d")
messages=[{"role": "user", "timestamp":"", "content": start_prompt_Daisy}]

class ContextHandlers:
	description = "A class for handling and managing messages in the chatGPT context object"
	
	def __init__(self, messages):
		self.messages = messages

	def get_context(self):
		"""Method for retrieving the messages object"""
		return self.messages
	
	def get_context_without_timestamp(self):
		"""Method for retrieving the messages object without the timestamp field"""
		messages_without_timestamp = []
		for message in self.messages:
			# create a copy of the message dictionary without the timestamp field
			message_without_timestamp = message.copy()
			del message_without_timestamp['timestamp']
			messages_without_timestamp.append(message_without_timestamp)
		return messages_without_timestamp
		
	def create_context(self):
		"""Method for creating a context with initial prompt"""
		self.messages = messages

	def single_message_context(self, role, message):
		return {'role': role, 'timestamp': timestamp, 'content': str(message)}

	def clear_context(self):
		"""Method for clearing the messages list"""
		self.messages = []

	def add_message_object(self, role, message):
		"""Method for adding a message object to the messages list with the given role and message"""
		logging.debug("Adding "+role+" message to context")
		now = dt.datetime.now() # get current datetime
		timestamp = now.strftime("%Y-%m-%d %H:%M:%S") # format datetime string
		new_message = {'role': role, 'timestamp': timestamp, 'content': str(message)}
		self.messages.append(new_message)
		logging.debug(self.messages)


	def remove_last_message_object(self):
		"""Method for removing the last message object from the messages list"""
		self.messages.pop()

	def get_last_message_object(self, user_type=None):
		"""Method for retrieving the last message object with the given role, or the last message object if no role is specified"""
		if user_type:
			for message in reversed(self.messages):
				if message['role'] == user_type:
					return message
		else:
			if self.messages:
				return self.messages[-1]
		return False

	def replace_last_message_object(self, message, user_type=None):
		"""Method for replacing the last message object with the given role"""
		if user_type:
			for i in reversed(range(len(self.messages))):
				if self.messages[i]['role'] == user_type:
					self.messages[i]['content'] = message
					return
		elif message and self.messages:
			self.messages[-1]['content'] = message

	def send_as_type(self, message, type):
		"""Method for adding a message to the context with the specified type"""
		self.messages.append({
			'content': message,
			'role': type,
			'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		})

	def delete_message_at_index(self, index):
		"""Method for deleting a message at the specified index"""
		try:
			index = int(index)
			if index < len(self.messages) and index >= 0:
				self.messages.pop(index)
				return True
		except ValueError:
			pass
		return False

	def update_message_at_index(self, message, index):
		"""Method for updating a message at the specified index"""
		try:
			index = int(index)
			if index < len(self.messages) and index >= 0:
				self.messages[index]['content'] = message
				self.messages[index]['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				return True
		except ValueError:
			pass
		return False

	"""
	get_messages(self)
	get_last_message(self)
	get_message_count(self)
	add_message_objects(self, messages)
	remove_message_object(self, index)
	set_message_object(self, index, role, message)
	"""

instance = ContextHandlers(constants.messages)
