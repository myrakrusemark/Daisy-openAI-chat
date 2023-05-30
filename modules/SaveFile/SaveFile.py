import logging
import os
import uuid
import dirtyjson
import re

class SaveFile:
    description = "A module for saving content to TXT, CSV, HTML, or PY file."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        data = dirtyjson.loads(arg)
        if "content" in data:
            filename = self.generate_unique_filename(data["filename"], data["filetype"])
            success = self.save_text_to_file(data['content'], filename)
            if success:
                output = "Text saved to file (" + filename + "):"
                output += "\n\n\"" + data['content']+"\""
                return output
            else:
                return "Error: Unable to save text to file. Please try again and match the argument format for the SaveFile command."
        else:
            return "Error: The argument was malformed. Please try again and match the argument format for the SaveFile command."
        


    def generate_unique_filename(self, filename_text, filetype_text):
        unique_id = str(uuid.uuid4())[:8]  # Generate a unique ID
        filename = "text_" + filename_text + "_" + unique_id + "."+filetype_text
        return filename

    def save_text_to_file(self, text, filename):
        try:
            with open(filename, "w") as file:
                file.write(text)
            return True
        except Exception as e:
            logging.error("TextSaver: Error saving text to file: " + str(e))
            return False
