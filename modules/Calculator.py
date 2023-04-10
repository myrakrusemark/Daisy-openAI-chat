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


		self.start_prompt = """You are a chatbot with a CALCULATOR. Any math expression you receive can be solved by sending it to the tool form, "Calculator". If I ask you any question that may require calculations, always respond using a "tool form" in the following format: [calculator: 5+5].
	Example #1:
	User: What is 53 percent of 1,203?
	Daisy: [calculator: 1203*.53]
	User: This is an automatic response to your tool form. Please respond to the user's last message using the information below.
		637.59
	Daisy: 53 percent of 1,203 is 637.59.

	Example #2:
	User: If I have 1500 ducklings and a wolf takes three quarters of them, how many do I have left?
	Daisy: [calculator: 1500*0.25]
	User: This is an automatic response to your tool form. Please respond to the user's last message using the information below.
		375
	Daisy: You have 375 ducklings left.

	"""
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
				new_prompt="This is an automatic response to your tool form. Please respond to the user's last message using the information below.\n"
				new_prompt += answer+"\n"

				self.ch.add_message_object('user', new_prompt)

				response_text = self.chat.request(self.ch.get_context_without_timestamp(), stop_event, stop_sound, True)
				print("RETURNING: "+response_text)
				return response_text
			
			else:
				return False
		else:
			return False


	def evaluate_expression(self, formula):
		"""Evaluates mathematical expressions"""
		return eval(formula)