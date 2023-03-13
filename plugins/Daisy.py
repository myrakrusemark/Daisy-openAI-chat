import asyncio
import signal
import os
import sys
import logging
import platform
import pvporcupine
import threading
from plugins import constants
import plugins.ChatSpeechProcessor as csp
import plugins.ConnectionStatus as cs
import plugins.ContextHandlers as ch
import plugins.SoundManager as sm
import plugins.Chat as chat
import plugins.Porcupine as porcupine




class Daisy:
    description = "Provides a user flow for Chat"
    module_hook = "Main_start"

    def __init__(self):

        self.csp = csp.instance
        self.cs = cs.instance
        self.ch = ch.instance
        self.sounds = sm.instance
        self.chat = chat.instance


        # Flag to indicate whether the warning message has already been logged
        self.internet_warning_logged = False

        #Instantiate ("daisy cancel") wake word
        keyword_paths = None
        if platform.system() == "Windows":
            keyword_paths = "plugins/daisy-cancel_en_windows_v2_1_0.ppn"
        elif platform.system() == "Linux":
            keyword_paths = "plugins/daisy-daisy_en_raspberry-pi_v2_1_0.ppn"
        else:
            logging.error("Unknown operating system, can't load wake word model.")
        self.porcupine_daisy_cancel = porcupine.Porcupine(
                        keyword_paths=keyword_paths,
                        sensitivities=0.5)

    def daisy_cancel(self):
        os.environ["CANCEL_LOOP"] = str(self.porcupine_daisy_cancel.run())

    def main(self):
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
                    logging.error("Error initializing Porcupine:", e)
                    continue

                if awoken:
                    self.sounds.play_sound_with_thread('alert')
                    sleep_word_detected = False


                    thread = threading.Thread(target=self.daisy_cancel)
                    thread.start()

                    os.environ["CANCEL_LOOP"] = "False"

                    while True:
                        
                        if thread.is_alive():
                            """
                            stt_text = self.csp.stt()

                            #Detect "Daisy cancel" and immediately break the loop
                            if stt_text == False:
                                self.sounds.play_sound_with_thread('end')
                                break

                            #Detect sleep word ("Bye bye, Daisy."), play a sound and respond with a goodbye
                            if self.csp.remove_non_alpha(stt_text) == self.csp.remove_non_alpha(constants.sleep_word):
                                logging.info("Done with conversation. Returning to wake word waiting.")
                                self.sounds.play_sound_with_thread('end')
                                sleep_word_detected = True

                            self.ch.add_message_object('user', stt_text)

                            text = self.chat.chat()

                            self.ch.add_message_object('assistant', text)

                            self.chat.display_messages()
                            
                            self.csp.tts(text)

                            #If 'Bye bye, Daisy' end the loop after response
                            if sleep_word_detected:
                                break
                            pass
                            """
                        else:
                            thread.join()
                            break

                    

            else:
                # Log a warning message if there is no internet connection and the warning hasn't already been logged
                if not self.internet_warning_logged:
                    logging.warning('No Internet connection. When a connection is available the script will automatically re-activate.')
                    self.internet_warning_logged = True

instance = Daisy()