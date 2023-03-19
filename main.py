import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import sys

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

# HOOK: Main_start
Main_start_hooks = {"Main_start_instances": ModuleLoader.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]
print("Main_start_instances:", Main_start_instances)

def sigint_handler(signal, frame):
    logging.info("Received Ctrl+C signal, terminating threads...")
    stop_event.set()

    for thread in threads:
        thread.join(timeout=1)  # Give threads 1 second to gracefully exit
    logging.info("All threads terminated.")
    sys.exit(0)

# Set the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)

stop_event = threading.Event()

def start_threads():
    threads = []
    for instance in Main_start_instances:
        print(instance)
        logging.info("Running Main_start_instances module: " + type(instance).__name__)

        # Start each thread with a reference to the shared memory object
        thread = threading.Thread(target=instance.main, args=(stop_event,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return threads

if __name__ == '__main__':
    if Main_start_instances:
        try:
            start_threads()
        except KeyboardInterrupt:
            logging.info("Received Ctrl+C signal, terminating threads...")
            sys.exit(0)
