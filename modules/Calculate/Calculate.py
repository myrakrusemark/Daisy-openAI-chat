import logging

class Calculate:
    description = "A module for evaluating mathematical expressions."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        logging.info("Calculator: Calculating: " + arg)
        answer = self.calculate_expression(arg)
        return answer

    def calculate_expression(self, expression):
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            logging.error("Calculator: Error evaluating expression: " + str(e))
            return "Error: Unable to evaluate the expression."

