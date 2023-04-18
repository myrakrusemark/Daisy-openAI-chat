import logging
import re

class Calculator:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module for evaluating mathematical expressions."
	module_hook = "Chat_request_inner"


	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.match = None

		self.start_prompt = 'You are a Calculator Bot: If I ask you a question that requires calculation, respond with a TOOL FORM as your only response, containing the expression: [Calculator: 5+5].  Then formulate your response based on the system message.'


	def start(self):

		logging.info("Calculator: Adding start prompt")
		self.ch.add_message_object_at_start('system', self.start_prompt)

	def check(self, text):
		logging.debug("Calculator: Checking for tool forms")
		found_tool_form = False
		if "[Calculator:" in text:
			self.match = re.search(r"\[Calculator:\s*(.*?)\]", text)
			if self.match:
				logging.info("Calculator: Found tool form")
				found_tool_form = True
		return found_tool_form

	def main(self, text, stop_event):
		#Find a search term in the response text (If --internet)
		processed_string = self.match.group()
		start = processed_string.index(":") + 1
		end = processed_string.index("]")
		expression = processed_string[start:end]

		logging.info("Calculator: Calculating: "+expression)

		answer = eval(expression)
		answer = str(answer)
		logging.info("Calculator: Answer: "+answer)
		prompt = "Respond using the answer below.\n"
		prompt += "Answer: "+answer+"\n"

		self.match = None

		return prompt
			
