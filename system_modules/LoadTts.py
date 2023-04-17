import threading
import time
import logging

class LoadTts(threading.Thread):
    def __init__(self, ext_instance, ml):
        threading.Thread.__init__(self)
        self.ml = ml
        self.ext_instance = ext_instance
        self.hook_instances = self.ml.get_hook_instances()


    def run(self):

        while "Tts" not in self.hook_instances:
            logging.info("Waiting for TTS hook...")
            self.hook_instances = self.ml.get_hook_instances() # Update hook_instances
            time.sleep(1)

        logging.debug("TTS hook found!")
        while len(self.hook_instances['Tts']) == 0:
            logging.info("Waiting for TTS module...")
            self.hook_instances = self.ml.get_hook_instances() # Update hook_instances
            time.sleep(1)

        logging.info("TTS module found! "+type(self.hook_instances["Tts"][0]).__name__)
        if len(self.hook_instances["Tts"]) > 1:
            logging.warning("Multiple TTS modules found. Only the first one will be used.: "+type(self.hook_instances["Tts"][0]).__name__)

        self.ext_instance.tts = self.hook_instances["Tts"][0]