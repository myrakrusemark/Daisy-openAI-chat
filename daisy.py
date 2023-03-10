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

#Init
sh = SignalHandlers()
#CTRL+C Signal Handler
signal.signal(signal.SIGINT, sh.signal_handler)

csp = ChatSpeechProcessor()
cs = ConnectionStatus()
ch = ContextHandlers(constants.messages)

modules = [{"name":"GoogleScraper", "module_hook":"Chat_chat_inner"}]
chat = Chat(os.environ["API_KEY"], ch.messages, modules, "plugins")

# Flag to indicate whether the warning message has already been logged
internet_warning_logged = False

def main():
    global internet_warning_logged  # Add this line to access the global variable

    while True:
        if cs.check_internet():
            # If internet connection is restored, log a message
            if internet_warning_logged:
                logging.info('Internet connection restored!')
                internet_warning_logged = False

            # Detect a wake word before listening for a prompt
            if csp.listen_for_wake_word():

                while True:
                    stt_text = csp.stt()

                    ch.add_message_object('user', stt_text)

                    text = chat.chat()

                    ch.add_message_object('assistant', text)

                    chat.display_messages()
                    
                    csp.tts(text)

                    #If 'Bye bye, Daisy' end the loop after response
                    if csp.remove_non_alpha(stt_text) == csp.remove_non_alpha(constants.sleep_word):
                        logging.info("Done with conversation. Returning to wake word waiting.")
                        break
        else:
            # Log a warning message if there is no internet connection and the warning hasn't already been logged
            if not internet_warning_logged:
                logging.warning('No Internet connection. When a connection is available the script will automatically re-activate.')
                internet_warning_logged = True

if __name__ == '__main__':
    main()