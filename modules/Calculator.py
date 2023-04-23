import logging
import math
import numpy
import datetime

class Calculator:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module for evaluating mathematical expressions."
	module_hook = "Chat_request_inner"
	tool_form_name = "Calculator"
	tool_form_description = """Uses eval() to evaluate any valid Python expression, such as arithmetic and logical operations, comparison operations, and function calls, as long as the expression is designed to produce a value and does not include statements or constructs that are not designed to produce a value. Additionally, if the expression involves functions or methods provided by external modules or packages (like 'math' or 'numpy' or 'datetime'), the required package would need to have its namespace specified in the expression, similar to the math module. Examples of such modules include numpy or scipy for complex mathematical or scientific computations, and datetime or time for working with dates and times."""
	tool_form_argument = "A python eval() solvable expression."

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch


	def main(self, arg, stop_event):
		logging.info("Calculator: Calculating: "+arg)

		answer = eval(arg)
		answer = str(answer)
		logging.info("Calculator: Answer: "+answer)

		return answer
			
