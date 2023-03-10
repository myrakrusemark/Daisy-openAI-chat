from . import constants
import logging

class ContextHandlers:
	description = "A class for handling and managing messages in the chatGPT context object"
	def __init__(self, messages):
		self.messages = messages

	
	def create_context(self):
		"""Method for creating a context with initial prompt"""
		self.messages = messages

	def clear_context(self):
		"""Method for clearing the messages list"""
		self.messages = []

	def add_message_object(self, role, message):
		"""Method for adding a message object to the messages list with the given role and message"""
		logging.debug("Adding "+role+" message to context")
		new_message = {'role': role, 'content': message}
		self.messages.append(new_message)
		logging.debug(self.messages)


	def remove_last_message_object(self):
		"""Method for removing the last message object from the messages list"""
		self.messages.pop()

	"""
	get_messages(self)
    get_last_message(self)
    get_message_count(self)
    add_message_objects(self, messages)
    remove_message_object(self, index)
    set_message_object(self, index, role, message)
    """