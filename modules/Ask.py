import logging

class Ask:
    description = "A module for getting text from the user's voice."
    module_hook = "Chat_request_inner"
    tool_form_name = "Ask"
    tool_form_description = """Ask the user a question."""
    tool_form_argument = "None"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        response = input(arg)
        return response
