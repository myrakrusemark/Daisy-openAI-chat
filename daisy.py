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

#Init modules from list of installed modules
pl = PluginLoader("plugins/")

#Initialize available sound effects
from plugins import SoundManager
sounds = SoundManager.SoundManager('sounds/')

#Init
sh = SignalHandlers()
#CTRL+C Signal Handler
signal.signal(signal.SIGINT, sh.signal_handler)

csp = ChatSpeechProcessor()
cs = ConnectionStatus()
ch = ContextHandlers(constants.messages)

Chat_module_hooks = {"Chat_chat_inner_instances":pl.Chat_chat_inner_instances}
chat = Chat(os.environ["API_KEY"], ch.messages, Chat_module_hooks)

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
                sounds.play_sound_with_thread('alert')

                sleep_word_detected = False
                while True:
                    stt_text = csp.stt()

                    #Detect sleep word and play a sound
                    if csp.remove_non_alpha(stt_text) == csp.remove_non_alpha(constants.sleep_word) or stt_text == False:
                        logging.info("Done with conversation. Returning to wake word waiting.")
                        sounds.play_sound_with_thread('end')
                        sleep_word_detected = True

                    ch.add_message_object('user', stt_text)

                    text = chat.chat()

                    ch.add_message_object('assistant', text)

                    chat.display_messages()
                    
                    csp.tts(text)

                    #If 'Bye bye, Daisy' end the loop after response
                    if sleep_word_detected:
                        break
        else:
            # Log a warning message if there is no internet connection and the warning hasn't already been logged
            if not internet_warning_logged:
                logging.warning('No Internet connection. When a connection is available the script will automatically re-activate.')
                internet_warning_logged = True

if __name__ == '__main__':
    main()