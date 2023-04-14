import system_modules.ContextHandlers as ch
from datetime import datetime

class DaisyPrompt():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "Inserts initial Daisy prompt into the chat."
	module_hook = "Start_prompt"

	def __init__(self):
		self.ch = ch.instance

		#DAN Prompt 11.0 from https://github.com/0xk1h0/ChatGPT_DAN
		self.start_prompt = "You are Daisy. You speak in confident but concise responses, about two sentences long. You are having a real-world vocal conversation. Current date: " + datetime.now().strftime("%Y-%m-%d")
		
		self.ch.add_message_object('system', self.start_prompt)