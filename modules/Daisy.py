import asyncio
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


import modules.RgbLed as led

class Daisy:
	description = "Provides a user flow for Chat"
	module_hook = "Main_start"

	def __init__(self):
		self.stop_event = threading.Event()

		self.csp = csp.instance
		self.cs = cs.instance
		self.ch = ch.instance
		self.sounds = sm.instance
		self.chat = chat.instance
		self.dm = dm.instance

		self.led = led.instance

		self.internet_warning_logged = False

	def close(self):
		self.stop_event.set()

	def main(self):
		self.sounds.play_sound("beep", 0.5)

		while not self.stop_event.is_set():

			if self.cs.check_internet():
				# If internet connection is restored, log a message
				if self.internet_warning_logged:
					logging.info('Internet connection restored!')
					self.internet_warning_logged = False

				# Detect a wake word before listening for a prompt
				awoken = False

				self.led.turn_on_color(0, 100, 0)  # Solid Green

				try:
					# Initialize Porcupine
					awoken = self.csp.listen_for_wake_word(self.stop_event)
				except Exception as e:
					# Catch the exception and handle it
					logging.error(f"Error initializing Porcupine: {e}")
					continue

				if awoken:
					self.led.breathe_color(100, 100, 100)  # Breathe Blue

					sleep_word_detected = False

					#HOOK: Daisy_wake
					try:
						import ModuleLoader as ml
						hook_instances = ml.instance.hook_instances
						if "Daisy_wake" in hook_instances:
							Daisy_wake_instances = hook_instances["Daisy_wake"]
							for instance in Daisy_wake_instances:
								logging.info("Running Daisy_start module: "+type(instance).__name__)
								response_text = instance.main()
						else:
							raise Exception("No Daisy_wake module found.")

					except Exception as e:
						logging.warning("Daisy_wake Hook error: "+str(e))

					thread = threading.Thread(target=self.dm.daisy_cancel, args=(self.stop_event,))
					thread.start()
					self.dm.set_cancel_loop(False)

					while not self.stop_event.is_set():
						if thread.is_alive():
							self.led.breathe_color(0, 0, 100)  # Breathe Blue
							stt_text = self.csp.stt(self.stop_event, 30) #30s timeout

							self.led.breathe_color(100,0,100)  # Breathe Blue

							self.ch.add_message_object('user', stt_text)

							if self.dm.get_cancel_loop():
								self.sounds.play_sound_with_thread('end', 1.0)
								break

							sound_stop_event = threading.Event()
							self.sounds.play_sound_with_thread('waiting', 0.2, self.stop_event, sound_stop_event)
							text = self.chat.request(self.ch.get_context_without_timestamp(), self.stop_event, sound_stop_event, True)
							
							self.ch.add_message_object('assistant', text)

							self.chat.display_messages()
							if self.dm.get_cancel_loop():
								self.sounds.play_sound_with_thread('end', 1.0)
								break

							self.led.breathe_color(100, 100, 100)  # Breathe White

						else:
							thread.join()
							break
			else:
				# Log a warning message if there is no internet connection and the warning hasn't been logged yet
				if not self.internet_warning_logged:
					self.led.turn_on_color(100, 0, 0)  # Solid Red
					logging.warning('No Internet connection. When a connection is available the script will automatically re-activate.')
					self.internet_warning_logged = True