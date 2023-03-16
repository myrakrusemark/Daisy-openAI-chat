import asyncio
import signal
import os
import multiprocessing as mp


import logging
logging.basicConfig(level=logging.INFO)

import ModuleLoader
import subprocess
import signal

import modules.ChatSpeechProcessor
import modules.Logging as l
from modules.SignalHandlers import SignalHandlers
from modules.ConnectionStatus import ConnectionStatus
from modules.Logging import Logging
from modules import constants
from modules.ContextHandlers import ContextHandlers
from modules.Chat import Chat

if os.environ["LED"]=="True":
    from modules.RgbLed import RgbLed

#Init
sh = SignalHandlers()
#CTRL+C Signal Handler
signal.signal(signal.SIGINT, sh.signal_handler)

#HOOK: Main_start
Main_start_hooks = {"Main_start_instances":ModuleLoader.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]
if Main_start_instances:
	for instance in Main_start_instances:
		if type(instance).__name__ == "Daisy":
			logging.info("Running Main_start_instances module: "+type(instance).__name__)
			instance.main()
Main_start_hooks = {"Main_start_instances":ModuleLoader.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]
'''

#HOOK: Main_start
Main_start_hooks = {"Main_start_instances":ModuleLoader.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]

# Define a shared memory object for storing data
shared_data = {"value": 42}

# List to hold the Popen objects for each subprocess
processes = []

def start_subprocesses():
    for instance in Main_start_instances:
        logging.info("Running Main_start_instances module: "+type(instance).__name__)
        # Start each subprocess with a reference to the shared memory object
        print(f"import modules.{type(instance).__name__} as {type(instance).__name__}; {type(instance).__name__}.instance.main(shared_data)")
        processes.append(subprocess.Popen(["python", "-c", f"import modules.{type(instance).__name__} as {type(instance).__name__}; {type(instance).__name__}.instance.main(shared_data)"]))
        break
# Handler for SIGINT signal
def sigint_handler(signal, frame):
    logging.info("Received Ctrl+C signal, terminating subprocesses...")
    for process in processes:
        process.terminate()
    logging.info("All subprocesses terminated.")
    exit(0)

# Set the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)

if Main_start_instances:
    start_subprocesses()

# Wait for all subprocesses to finish
for process in processes:
    process.wait()

# Use the shared data object in the main process
logging.info(f"Shared data: {list(shared_data)}")
'''
