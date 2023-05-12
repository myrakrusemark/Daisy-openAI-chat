import logging
import os
import uuid
import json
import re

class SaveText:
    description = "A module for saving text to a file with a unique name."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        data = json.loads(arg)
        filename = self.generate_unique_filename(data["filename"])
        success = self.save_text_to_file(data['text'], filename)
        if success:
            return "Text saved to file: " + filename
        else:
            return "Error: Unable to save text to file."

    def generate_unique_filename(self, filename_text):
        unique_id = str(uuid.uuid4())[:8]  # Generate a unique ID
        filename = "text_" + filename_text + "_" + unique_id + ".txt"
        return filename

    def save_text_to_file(self, text, filename):
        try:
            with open(filename, "w") as file:
                file.write(text)
            return True
        except Exception as e:
            logging.error("TextSaver: Error saving text to file: " + str(e))
            return False
