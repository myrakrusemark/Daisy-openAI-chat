import os
from django.core.management import execute_from_command_line
import threading
from wsgiref.simple_server import WSGIRequestHandler

import system_modules.Chat as chat


class WebConfigDjango:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	#NOTE: This module cannot currently gracefully shutdown. Daisy must be restarted to stop the server.
	
	description = "A module that serves a web page."
	module_hook = "Main_start"

	def __init__(self, ml, settings_module="modules.WebConfigDjango.core.settings"):
		self.ml = ml
		self.ch = ml.ch
		self.chat = chat.Chat(self.ml, self.ch)

		self.settings_module = settings_module
		self.server = None

		self.stop_event = threading.Event()

	def close(self):
		self.stop_event.set()
		if self.server:
			self.server.shutdown()

	def main(self):
		print("🌎 DAISY - Web Config 🖥️")

		# Store ml, ch, and chat in the global scope
		global GLOBAL_ML, GLOBAL_CH, GLOBAL_CHAT
		GLOBAL_ML = self.ml
		GLOBAL_CH = self.ch
		GLOBAL_CHAT = self.chat

		#Start the server
		os.environ.setdefault("DJANGO_SETTINGS_MODULE", self.settings_module)
		argv = ['modules/WebConfigDjango/manage.py', 'runserver', '--noreload']
		handler = WSGIRequestHandler
		self.server = execute_from_command_line(argv)

