import logging
from modules.Logging import Logging

logger = Logging('daisy.log')
logger.set_up_logging()

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import ModuleLoader as ml
import modules.ChatSpeechProcessor
from modules.SignalHandlers import SignalHandlers
from modules.ConnectionStatus import ConnectionStatus

from modules import constants
from modules.Chat import Chat

if os.environ.get("LED") == "True":
	from modules.RgbLed import RgbLed

# HOOK: Main_start
hook_instances = ml.instance.hook_instances
if hook_instances["Main_start"]:
	Main_start_instances = hook_instances["Main_start"]

def start_threads():
	with ThreadPoolExecutor() as executor:
		futures = []
		for instance in Main_start_instances:
			logging.info("Running Main_start_instances module: %s", type(instance).__name__)
			future = executor.submit(instance.main, stop_event)
			futures.append(future)

		# Wait for all tasks to complete
		for i, future in enumerate(futures):
			try:
				result = future.result()
				logging.info("Thread %d output: %s", i, result)
			except Exception:
				logging.exception("An exception occurred while running a module")

if __name__ == "__main__":
	stop_event = threading.Event()
	try:
		start_threads()
	except KeyboardInterrupt:
		logging.info("Received Ctrl+C signal, terminating threads...")
		stop_event.set()
		logging.info("All threads terminated.")
		sys.exit(0)
