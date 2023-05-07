import logging
import os
import uuid
import re

class TextSaver:
    description = "A module for saving text to a file with a unique name."
    module_hook = "Chat_request_inner"
    tool_form_name = "Save Text To File"
    tool_form_description = "This command takes one argument, which should be a string of text. The text will be saved to a file."
    tool_form_argument = "String of text"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        logging.info("TextSaver: Saving text to file...")
        filename = self.generate_unique_filename(arg)
        success = self.save_text_to_file(arg, filename)
        if success:
            return "Text saved to file: " + filename
        else:
            return "Error: Unable to save text to file."

    def generate_unique_filename(self, arg):
        unique_id = str(uuid.uuid4())[:8]  # Generate a unique ID
        filename_pattern = r"\{(.+?)\}"
        match = re.search(filename_pattern, arg)
        filename_text = match.group(1) if match else "untitled"
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
