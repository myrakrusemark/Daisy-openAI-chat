import logging

class Ask:
    description = "A module for getting text from the user's voice."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        response = input(arg)
        return response
