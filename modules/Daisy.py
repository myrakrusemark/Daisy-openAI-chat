import asyncio
import signal
import sys
import logging
import platform
import pvporcupine
import threading
import os
from modules import constants
import modules.ChatSpeechProcessor as csp
import modules.ConnectionStatus as cs
import modules.ContextHandlers as ch
import modules.SoundManager as sm
import modules.Chat as chat
import modules.Porcupine as porcupine
import modules.DaisyMethods as dm

if os.environ["LED"]=="True":
    from modules.RgbLed import RgbLed

class Daisy:
    description = "Provides a user flow for Chat"
    module_hook = "Main_start"

    def __init__(self):
        self.csp = csp.instance
        self.cs = cs.instance
        self.ch = ch.instance
        self.sounds = sm.instance
        self.chat = chat.instance
        self.dm = dm.instance

        if os.environ["LED"]=="True":
                self.led = led.instance

        self.internet_warning_logged = False
        
    def main(self):
        # Access the shared data dictionary and print the value of the "value" key
        #print("Shared data value in subprocess:", shared_data["value"])

        #global internet_warning_logged  # Add this line to access the global variable
        while True:
            if self.cs.check_internet():
                # If internet connection is restored, log a message
                if self.internet_warning_logged:
                    logging.info('Internet connection restored!')
                    self.internet_warning_logged = False

                # Detect a wake word before listening for a prompt
                awoken=False

                if os.environ["LED"]=="True":
                    self.led.breathe_color(0,0,100)
                self.sounds.play_sound("beep", 0.5)

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


                    thread = threading.Thread(target=self.dm.daisy_cancel)
                    thread.start()

                    self.dm.set_cancel_loop(False)

                    while True:
                        if thread.is_alive():
                            
                            stt_text = self.csp.stt()
                            #get_cancel_loop is already part of stt()

                            
                            #Detect sleep word ("Bye bye, Daisy."), play a sound and give Daisy a chance to respond with a goodbye
                            if self.csp.remove_non_alpha(stt_text) == self.csp.remove_non_alpha(constants.sleep_word):
                                logging.info("Done with conversation. Returning to wake word waiting.")
                                self.sounds.play_sound_with_thread('end')
                                sleep_word_detected = True

                            self.ch.add_message_object('user', stt_text)
                            if self.dm.get_cancel_loop():
                                self.sounds.play_sound_with_thread('end')
                                break

                            text = self.chat.chat()
                            if self.dm.get_cancel_loop():
                                self.sounds.play_sound_with_thread('end')
                                break

                            self.ch.add_message_object('assistant', text)
                            if self.dm.get_cancel_loop():
                                self.sounds.play_sound_with_thread('end')
                                break

                            self.chat.display_messages()
                            if self.dm.get_cancel_loop():
                                self.sounds.play_sound_with_thread('end')
                                break

                            self.csp.tts(text)
                            #get_cancel_loop is already part of play_sound()

                            #If 'Bye bye, Daisy' end the loop after response
                            if sleep_word_detected:
                                self.dm.set_cancel_loop(True)
                                break
                            pass
                            
                        else:
                            thread.join()
                            break

                    

            else:
                # Log a warning message if there is no internet connection and the warning hasn't already been logged
                if not self.internet_warning_logged:
                    logging.warning('No Internet connection. When a connection is available the script will automatically re-activate.')
                    self.internet_warning_logged = True

instance = Daisy()