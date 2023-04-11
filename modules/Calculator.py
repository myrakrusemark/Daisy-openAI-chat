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


		self.start_prompt = """You are a calculatorbot. If I ask you a question that requires calculation, respond using a "tool form" in the following format:
		
		[calculator: 5+5]."""

		logging.info("Calculator: Adding start prompt")
		self.ch.add_message_object('system', self.start_prompt)


	def main(self, text, stop_event, stop_sound):
		#Find a search term in the response text (If --internet)
		logging.debug("Calculator: Checking for tool forms")
		if "[calculator:" in text.lower():
			match = re.search(r"\[calculator:.*\]", text)
			if match:
				processed_string = match.group()
				start = processed_string.index(":") + 1
				end = processed_string.index("]")
				expression = processed_string[start:end]

				logging.info("Calculator: Calculating: "+expression)

				answer = self.evaluate_expression(expression)
				answer = str(answer)
				new_prompt="Respond using the answer below.\n"
				new_prompt += "Answer: "+answer+"\n"

				self.ch.add_message_object('system', new_prompt)

				response_text = self.chat.request(self.ch.get_context_without_timestamp(), stop_event, stop_sound, True)
				return response_text
			
			else:
				return False
		else:
			return False


	def evaluate_expression(self, formula):
		"""Evaluates mathematical expressions"""
		return eval(formula)