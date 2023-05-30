import logging

class TakeNote:
    description = "Keeping track of temporary information while working on complex tasks"
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        return arg