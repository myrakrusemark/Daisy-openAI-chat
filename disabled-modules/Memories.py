
class Memories:
	description = "A module for finding and talking about saved conversations."
	module_hook = "Chat_request_inner"
	tool_form_name = "Review Memories"
	tool_form_description = "A module that finds and talks about past conversations."
	tool_form_argument = "Search term"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.match = None


	def main(self, arg, stop_event):
		rows = self.ch.get_conversation_name_summary(limit=25)
		if rows:
			output = ""
			for i, (id, name, summary) in enumerate(rows):
				output += f"Conversation {i+1} ID: {id}\n"
				output += f"Conversation {i+1} Name: {name}\n"
				output += f"Conversation {i+1} Summary: {summary}\n\n"
		else:
			output = f"No conversations found."

		return output