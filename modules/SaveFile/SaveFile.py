import logging
import uuid
import dirtyjson
import subprocess
import sys
import os

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
            success = self.save_file(data['content'], filename)
            if success:
                output = "Text saved to file (" + filename + "):"
                output += "\n\n\"" + data['content'] + "\""

                self.open_file_with_default_app(filename)

                return output
            else:
                return "Error: Unable to save text to file. Please try again and match the argument format for the SaveFile command."
        else:
            return "Error: The argument was malformed. Please try again and match the argument format for the SaveFile command."

    def generate_unique_filename(self, filename_text, filetype_text):
        unique_id = str(uuid.uuid4())[:8]  # Generate a unique ID
        filename = "text_" + filename_text + "_" + unique_id + "." + filetype_text
        return filename

    def save_file(self, text, filename):
        try:
            output_dir = "SaveFile output"
            os.makedirs(output_dir, exist_ok=True)  # Create the output directory if it doesn't exist

            output_path = os.path.join(output_dir, filename)  # Combine the directory path and filename
            with open(output_path, "w", encoding='utf-8') as file:
                file.write(text)
            return True
        except Exception as e:
            logging.error("TextSaver: Error saving text to file: " + str(e))
            return False


    def open_file_with_default_app(self, file_path):
        try:
            output_dir = "SaveFile output"
            full_file_path = os.path.join(output_dir, file_path)  # Combine the directory path and file path

            if sys.platform.startswith('darwin'):  # macOS
                subprocess.call(('open', full_file_path))
            elif sys.platform.startswith('win32'):  # Windows
                os.startfile(full_file_path)
            else:  # Linux/other
                subprocess.call(('xdg-open', full_file_path))
        except Exception as e:
            print("Unable to open file with default application:", str(e))