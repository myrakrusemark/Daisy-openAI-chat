import logging

class Ask:
    description = "A module for getting text from the user's voice."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch
        self.im = ml.im

    def main(self, arg, stop_event):
        return "Asking a question to the user..."
