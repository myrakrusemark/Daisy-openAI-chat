import asyncio
import signal
import os

import logging
logging.basicConfig(level=logging.INFO)

from plugins.ChatSpeechProcessor import ChatSpeechProcessor
from plugins.SignalHandlers import SignalHandlers
from plugins.ConnectionStatus import ConnectionStatus
from plugins.Logging import Logging
from plugins import constants
from plugins.ContextHandlers import ContextHandlers
from plugins.Chat import Chat
from PluginLoader import PluginLoader

#Init
sh = SignalHandlers()
#CTRL+C Signal Handler
signal.signal(signal.SIGINT, sh.signal_handler)

#Init modules from list of installed modules
pl = PluginLoader("plugins/")
Chat_module_hooks = {"Chat_chat_inner_instances":pl.Chat_chat_inner_instances}

#Initiate main program, Chat, to be passed to the Main_start module(s).
chat = Chat(os.environ["API_KEY"], Chat_module_hooks)

#HOOK: Main_start
Main_start_hooks = {"Main_start_instances":pl.Main_start_instances}
Main_start_instances = Main_start_hooks["Main_start_instances"]
if Main_start_instances:
	for instance in Main_start_instances:
		logging.info("Running Main_start_instances plugin: "+type(instance).__name__)
		instance.main(chat)

