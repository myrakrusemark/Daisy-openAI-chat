import asyncio
import signal
import os

import logging
logging.basicConfig(level=logging.INFO)

import PluginLoader


import plugins.ChatSpeechProcessor
import plugins.Logging as l
from plugins.SignalHandlers import SignalHandlers
from plugins.ConnectionStatus import ConnectionStatus
from plugins.Logging import Logging
from plugins import constants
from plugins.ContextHandlers import ContextHandlers
from plugins.Chat import Chat


#Init
sh = SignalHandlers()
#CTRL+C Signal Handler
signal.signal(signal.SIGINT, sh.signal_handler)


#HOOK: Main_start
Main_start_hooks = {"Main_start_instances":PluginLoader.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]
if Main_start_instances:
	for instance in Main_start_instances:
		logging.info("Running Main_start_instances plugin: "+type(instance).__name__)
		instance.main()

