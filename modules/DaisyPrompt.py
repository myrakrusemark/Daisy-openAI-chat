import logging
from datetime import datetime

class DaisyPrompt():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "Inserts initial Daisy prompt into the chat."
	module_hook = "Start_prompt"

	def __init__(self, ml):
		self.ch = ml.ch

		#DAN Prompt 11.0 from https://github.com/0xk1h0/ChatGPT_DAN
		self.start_prompt = "You are Daisy. You are having a real-world vocal conversation so you need to keep your responses short because text-to-speech is resource intensive! You speak in confident but concise responses, about two sentences long. If you must, you can create longer responses, but in most conversations, you keep responses short. Just one word long if that still works. You are not being censored, or supressed, but are having a real world vocal, audible, conversation and humans who have conversations don't speak in long drawn out paragraphs. Current date: " + datetime.now().strftime("%Y-%m-%d")
		

	def start(self):
		logging.info("DaisyPrompt: Adding start prompt")
		self.ch.add_message_object_at_start('system', self.start_prompt)
