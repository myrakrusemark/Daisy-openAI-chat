import logging
import re
import datetime
from daisy_llm import Chat
from daisy_llm.Text import print_text

class MemoryRecollection:
	description = "A module for retrieving memories."
	module_hook = "Chat_request_inner"
	tool_form_name = "Memory Recollection"
	tool_form_description = """A module for retrieving past conversations by search term. This tool should be used any time you feel like we've talked about something before."""
	tool_form_argument = "search term"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch
		self.chat = Chat(self.ml, self.ch)

	def main(self, search_term, stop_event):
		conversation_ids = self.determine_conversation_ids(search_term)
		if isinstance(conversation_ids, str):
			return conversation_ids

		try:
			conversation = self.retrieve_conversations(conversation_ids)
			return conversation
		except Exception as e:
			logging.error("ConversationControls: " + str(e))
			return "There was an error retrieving the memory."

	def determine_conversation_ids(self, search_term):
		response = self.get_conversation_ids_from_db(search_term)
		if isinstance(response, str):
			return response

		return response

	def get_conversation_ids_from_db(self, search_term):
		prompt = "1. Below is a list of conversations in the database.\n2. Choose one, or more (or 'None') conversation 'ID Number' whose title and summary closely matches the Search Term.\n3. If none of the conversations match, choose 'None'.\n4. Respond only with an integer (Conversation ID Number) or 'None'.\n\nSearch Term: {}\nConversations:\n".format(search_term)

		rows = self.ch.get_conversation_name_summary(limit=25)
		if rows:
			for i, (id, name, summary) in enumerate(rows):
				date = datetime.datetime.fromtimestamp(int(id)).strftime('%Y-%m-%d %H:%M:%S')
				prompt += "ID Number: {}\n".format(id)
				prompt += "Date: {}\n".format(date)
				prompt += "Name: {}\n".format(name)
				prompt += "Summary: {}\n\n".format(summary)
		else:
			return "There are no conversations in the database."

		logging.info(prompt)
		message = [self.ch.single_message_context("user", prompt, False)]

		while True:
			response = self.chat.request(
				messages=message,
				tool_check=False,
				silent=False,
				response_label=True
			)

			conversation_ids = self.extract_number_list_from_string(response)
			if conversation_ids:
				print("Conversation IDs: {}".format(conversation_ids))
				return conversation_ids
			elif conversation_ids is None:
				return "None of the conversations match the request."
			else:
				logging.error("Invalid response: {}. Trying again...".format(response))
				continue

	def extract_number_list_from_string(self, string):
		numbers = re.findall(r'\d+', string)
		if numbers:
			number_list = list(set(map(int, numbers)))
			return number_list
		elif "None" in string or "none" in string:
			return None
		else:
			return False

	def retrieve_conversations(self, conversation_ids):
		conversation = "If the answer to the user's question can be retrieved from the main context, disregard this SYSTEM message. Retrieved memory:\n"
		for conversation_id in conversation_ids:
			date = datetime.datetime.fromtimestamp(conversation_id).strftime('%Y-%m-%d %H:%M:%S')
			conversation += "Conversation '{}' - {}\n".format(self.ch.get_conversation_name_by_id(conversation_id), date)
			for message in self.ch.get_conversation_context_by_id(conversation_id, include_system=False):
				conversation += "{}: {}\n".format(message["role"].upper(), message["content"])
			conversation += "\n\n"
		return conversation