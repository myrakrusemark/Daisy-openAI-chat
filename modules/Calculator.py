import logging
import re

class Calculator:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module for evaluating mathematical expressions."
	module_hook = "Chat_request_inner"
	tool_form_name = "Calculator"
	tool_form_description = "A module that calculates mathematical expressions."
	tool_form_argument = "Mathematical Expression"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.match = None


	def main(self, arg, stop_event):
		logging.info("Calculator: Calculating: "+arg)

		answer = eval(arg)
		answer = str(answer)
		logging.info("Calculator: Answer: "+answer)


		self.match = None

		return answer
			
