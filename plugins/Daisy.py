import asyncio
import signal
import os
import sys
import logging

from plugins import constants
from plugins.ChatSpeechProcessor import ChatSpeechProcessor
from plugins.SignalHandlers import SignalHandlers
from plugins.ConnectionStatus import ConnectionStatus
from plugins.Logging import Logging
from plugins.ContextHandlers import ContextHandlers
from plugins.SoundManager import SoundManager
from PluginLoader import PluginLoader
from plugins.Chat import Chat

class Daisy:
    description = "Provides a user flow for Chat"
    module_hook = "Main_start"

    def __init__(self):

        #Initialize available sound effects
        self.sounds = SoundManager('sounds/')

        self.csp = ChatSpeechProcessor()
        self.cs = ConnectionStatus()
        self.ch = ContextHandlers(constants.messages)

        # Flag to indicate whether the warning message has already been logged
        self.internet_warning_logged = False

    def main(self, chat):
        #global internet_warning_logged  # Add this line to access the global variable

        self.sounds.play_sound("beep", 0.5)
        while True:
            if self.cs.check_internet():
                # If internet connection is restored, log a message
                if self.internet_warning_logged:
                    logging.info('Internet connection restored!')
                    self.internet_warning_logged = False

                # Detect a wake word before listening for a prompt
                awoken=False
                try:
                    # Initialize Porcupine
                    awoken = self.csp.listen_for_wake_word()
                except Exception as e:
                    # Catch the exception and handle it
                    print("Error initializing Porcupine:", e)
                    continue

                if awoken:
                    self.sounds.play_sound_with_thread('alert')

                    sleep_word_detected = False
                    while True:
                        stt_text = self.csp.stt()

                        #Detect sleep word and play a sound
                        if self.csp.remove_non_alpha(stt_text) == self.csp.remove_non_alpha(constants.sleep_word) or stt_text == False:
                            logging.info("Done with conversation. Returning to wake word waiting.")
                            self.sounds.play_sound_with_thread('end')
                            sleep_word_detected = True

                        self.ch.add_message_object('user', stt_text)

                        text = chat.chat()

                        self.ch.add_message_object('assistant', text)

                        chat.display_messages()
                        
                        self.csp.tts(text)

                        #If 'Bye bye, Daisy' end the loop after response
                        if sleep_word_detected:
                            break
            else:
                # Log a warning message if there is no internet connection and the warning hasn't already been logged
                if not self.internet_warning_logged:
                    logging.warning('No Internet connection. When a connection is available the script will automatically re-activate.')
                    self.internet_warning_logged = True

