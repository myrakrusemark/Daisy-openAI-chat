import asyncio
import signal
import os

import logging
logging.basicConfig(level=logging.INFO)

import ModuleLoader


import modules.ChatSpeechProcessor
import modules.Logging as l
from modules.SignalHandlers import SignalHandlers
from modules.ConnectionStatus import ConnectionStatus
from modules.Logging import Logging
from modules import constants
from modules.ContextHandlers import ContextHandlers
from modules.Chat import Chat


#Init
sh = SignalHandlers()
#CTRL+C Signal Handler
signal.signal(signal.SIGINT, sh.signal_handler)


#HOOK: Main_start
Main_start_hooks = {"Main_start_instances":ModuleLoader.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]
if Main_start_instances:
	for instance in Main_start_instances:
		logging.info("Running Main_start_instances module: "+type(instance).__name__)
		instance.main()

