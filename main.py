import logging
from modules.Logging import Logging

logger = Logging('daisy.log')
logger.set_up_logging()

import os
import sys
import threading
import time
import concurrent.futures

import ModuleLoader as ml
import modules.ChatSpeechProcessor
from modules.Logging import Logging
from modules.SignalHandlers import SignalHandlers
from modules.ConnectionStatus import ConnectionStatus
from modules import constants
from modules.Chat import Chat

if os.environ.get("LED") == "True":
	from modules.RgbLed import RgbLed


# Define a function that starts a new thread for a given hook instance
def start_instance(instance):
	logging.info("Main_start: Running %s module: %s", instance.__class__.__name__, type(instance).__name__)
	future = executor.submit(instance.main)
	return future

# Define a dictionary to keep track of running threads
running_threads = {}
stop_event = threading.Event()
# Create the ThreadPoolExecutor outside the while loop
with concurrent.futures.ThreadPoolExecutor() as executor:
	# Main loop that watches for changes to hook_instances["Main_start"]
	while True:
		logging.debug("Main_start: Checking for changes...")
		if list(running_threads.keys()):
			future_object = list(running_threads.values())[0]  # get the Future object from the dictionary
			if future_object.exception() is not None:  # check if the Future object has a raised exception
				runtime_error = future_object.exception()  # get the raised exception from the Future object
				logging.error("An error occurred: %s", str(future_object.exception()))


		hook_instances = ml.instance.get_hook_instances()
		# Check if any new hook instances have been added or removed
		if "Main_start" in hook_instances:
			for instance in hook_instances["Main_start"]:
				for module in ml.instance.get_available_modules():
					if module['class_name'] == instance.__module__ and instance not in running_threads:
						if module['enabled']:
							future = executor.submit(start_instance, instance)
							running_threads[instance] = future
						else:
							future = running_threads[instance]
							future.cancel()
							del running_threads[instance]


		# Wait for some time before checking for updates again
		time.sleep(1)
