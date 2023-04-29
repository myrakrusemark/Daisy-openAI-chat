import logging
import re
from daisy_llm import Chat
from daisy_llm.Text import print_text

class MemoryManagement:
	description = "A module for handling and manipulating conversations."
	module_hook = "Chat_request_inner"
	tool_form_name = "Memory Management"
	tool_form_description = """A module for retrieving, handling and manipulating past conversation. Can create a new conversation, or retrieve a conversation by search term."""
	tool_form_argument = "new, retrieve(search term)"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch
		self.chat = Chat(self.ml, self.ch)

	def main(self, arg, stop_event):

		if arg == "new":
			self.ch.new_conversation()
			return "New conversation created."

		elif arg.startswith("retrieve(") and arg.endswith(")"):
			search_term = arg[9:-1]

			#Get the conversation ID
			arg = self.determine_conversation_id(search_term)
			if type(arg) is not int:
				return arg

			try:
				name = self.ch.get_conversation_name_by_id(int(arg))
			except Exception as e:
				logging.error("ConversationControls: "+str(e))
				name = "Unknown"

			#Switch to the conversation
			self.ch.set_conversation_by_id(arg)
			return "Switched to conversation: "+str(name)

		return "There was an error."
			

	def determine_conversation_id(self, search_term):
		#Get the conversation ID
		response = "None"
		
		#Get the conversation ID from the conversation
		prompt = """1. Below is a list of conversations in the database.
2. Choose one (or "None") conversation "ID Number" whose title and summary closely matches the Search Term.
3. If none of the conversations match, choose "None".
4. Respond only with an integer (Conversation ID Number) or "None".

Search Term: """+search_term+"""
Conversations:
"""
		rows = self.ch.get_conversation_name_summary(limit=25)
		if rows:
			for i, (id, name, summary) in enumerate(rows):
				prompt += f"ID Number: {id}\n"
				prompt += f"Name: {name}\n"
				prompt += f"Summary: {summary}\n\n"
		else:
			return "There are no conversations in the database."
		
		message = [self.ch.single_message_context("user", prompt, False)]
		#print(message)
	
		conversation_id = None
		while True:
			response = self.chat.request(
				messages=message, 
				tool_check=False,
				silent=False,
				response_label=True
				)
			
			conversation_id = self.extract_number_from_string(response)

			if conversation_id is not None:
				print("Conversation ID: "+str(conversation_id))
				break
			if "None" in response:
				return "None of the conversation match the request."

		#Confirm the conversation exists by getting its name
		try:
			name = self.ch.get_conversation_name_by_id(conversation_id)
			print_text("Conversation found: "+str(name)+" ("+response+")", "green")

			return_conversation = "Retrieved memory:\n"
			for message in self.ch.get_conversation_context_by_id(conversation_id):
				return_conversation += message["role"].upper()+": "+message["content"]+"\n"

			return return_conversation
		except Exception as e:
			logging.error("Conversation Controls: "+str(e))
			return "Sorry, a conversation could not be found. (get_conversation_name_by_id("+arg+"))"
			
	def extract_number_from_string(self, string):
		# Use regex to search for a number in the string
		match = re.search(r'\d+', string)
		if match:
			# Extract the matched number
			number = int(match.group())
			return number
		else:
			return None