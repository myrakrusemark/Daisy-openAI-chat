import logging

class Chained:
    description = "A module for evaluating mathematical expressions."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        print("STEP BY STEP")


