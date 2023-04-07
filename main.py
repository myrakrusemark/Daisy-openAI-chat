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
				logging.error(runtime_error)  # print the raised exception

		hook_instances = ml.instance.get_hook_instances()
		# Check if any new hook instances have been added or removed
		if "Main_start" in hook_instances and set(hook_instances["Main_start"]) != set(list(running_threads.keys())):
			# Get the new instances
			new_instances = list(set(hook_instances["Main_start"]) - set(list(running_threads.keys())))
			# Start a new thread for each new instance
			for instance in new_instances:
				future = executor.submit(start_instance, instance)
				running_threads[instance] = future

			# Get the instances that have been removed
			removed_instances = list(set(running_threads.keys()) - set(hook_instances["Main_start"]))
			# Stop the threads for each removed instance
			for instance in removed_instances:
				if instance in running_threads:
					future = running_threads[instance]
					future.cancel()
					del running_threads[instance]

		# Wait for some time before checking for updates again
		time.sleep(1)

'''
if __name__ == "__main__":
	stop_event = threading.Event()
	try:
		pass  # No threads need to be started here as they are started by the loop
	except KeyboardInterrupt:
		logging.info("Received Ctrl+C signal, terminating threads...")
		stop_event.set()
		logging.info("All threads terminated.")
		sys.exit(0)
'''
