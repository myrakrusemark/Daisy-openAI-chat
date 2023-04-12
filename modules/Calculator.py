import logging
import re

import modules.ContextHandlers as ch
import modules.ChatSpeechProcessor as csp
import modules.Chat as chat



class Calculator:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module for evaluating mathematical expressions."
	module_hook = "Chat_request_inner"


	def __init__(self):

		self.ch = ch.instance
		self.csp = csp.instance
		self.chat = chat.instance
		self.match = None


		self.start_prompt = """You are a calculatorbot. If I ask you a question that requires calculation, respond using a "tool form" in the following format:
		
		[calculator: 5+5]."""

		logging.info("Calculator: Adding start prompt")
		self.ch.add_message_object('system', self.start_prompt)

	def check(self, text):
		logging.debug("Calculator: Checking for tool forms")
		found_tool_form = False
		if "[calculator:" in text.lower():
			self.match = re.search(r"\[calculator:\s*(.*?)\]", text)
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
			
