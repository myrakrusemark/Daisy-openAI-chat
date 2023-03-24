from modules import constants
import logging

class ContextHandlers:
	description = "A class for handling and managing messages in the chatGPT context object"
	
	def __init__(self, messages):
		self.messages = messages

	def get_context(self):
		"""Method for retrieving the messages object"""
		return self.messages
		
	def create_context(self):
		"""Method for creating a context with initial prompt"""
		self.messages = messages

	def clear_context(self):
		"""Method for clearing the messages list"""
		self.messages = []

	def add_message_object(self, role, message):
		"""Method for adding a message object to the messages list with the given role and message"""
		logging.debug("Adding "+role+" message to context")
		new_message = {'role': role, 'content': str(message)}
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

	"""
	get_messages(self)
	get_last_message(self)
	get_message_count(self)
	add_message_objects(self, messages)
	remove_message_object(self, index)
	set_message_object(self, index, role, message)
	"""

instance = ContextHandlers(constants.messages)