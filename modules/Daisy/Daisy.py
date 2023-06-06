import logging
import threading

import daisy_llm.ChatSpeechProcessor as csp
import daisy_llm.SoundManager as sm
import daisy_llm.Chat as chat

from daisy_llm.Text import print_text

from modules.Daisy.DaisyMethods import listen_for_daisy_cancel, check_internet, wait_for_wake_word_or_input
import modules.RgbLed as led

class Daisy:
	description = "Provides a user flow for Chat"
	module_hook = "Main_start"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch
		self.im = ml.im
		self.commh = ml.commh

		self.chat = None
		self.csp = csp.ChatSpeechProcessor(self.ml)
		self.sounds = sm.SoundManager()
		self.led = led.RgbLed()

		self.threads = []
		self.daisy_stop_event = threading.Event()
		self.awake_stop_event = threading.Event()
		self.dc_t = None

		self.internet_warning_logged = False

		#Handle global text input
		self.text_input_thread = None
		self.text_input_result = None

	def main(self):
		self.sounds.play_sound("beep", 0.5)
		print_text("🌼 DAISY - Voice Assistant 🌼", "pink", "\n")

		self.chat = chat.Chat(self.ml, self.csp)

		check_internet(self.awake_stop_event, self.daisy_stop_event, self.threads)

		self.awake_stop_event.clear()

		self.ch.load_context()

		continue_conversation = False
		sound = True
		awake_or_text = None
		while not self.daisy_stop_event.is_set():

			#Wait for wake word or get input from the keyboard
			self.awake_stop_event.clear()
			awake_or_text = wait_for_wake_word_or_input(
				im=self.im, 
				continue_conversation=continue_conversation, 
				sound=sound,
				daisy_stop_event=self.daisy_stop_event, 
				led=self.led
				)
			continue_conversation = False

			self.handle_wake()
			self.led.breathe_color(0, 0, 100)  # Breathe Blue

			#Get input
			input_text = None
			if type(awake_or_text) == bool:
				input_text = self.csp.stt(self.awake_stop_event) #30s timeout
				sound = True
			elif type(awake_or_text) == str:
				input_text = awake_or_text
				sound = False

			if self.awake_stop_event.is_set():
				awake_or_text = self.handle_sleep(sound)
				continue

			response = None
			if input_text:
				self.led.breathe_color(100,0,100)  # Breathe Blue #NEEDS CANCEL LOOP

				self.ch.add_message_object('user', input_text)

				if self.awake_stop_event.is_set():
					awake_or_text = self.handle_sleep(sound)
					continue

				sound_stop_event = threading.Event()
				if sound:
					self.sounds.play_sound_with_thread(
						name_or_bytes='waiting', 
						volume=0.2, 
						awake_stop_event=self.awake_stop_event, 
						sound_stop_event=sound_stop_event
						)

				#Determine and run commands
				commands_output = "None"
				messages = self.ch.get_context(include_timestamp=False, include_system=False)

				try:
					commands_output = self.chat.determine_and_run_commands(
						messages=self.ch.get_context_without_timestamp(), 
						tts=sound
						)
				except Exception as e:
					logging.error("determine_and_run_commands error: "+ str(e))

				if commands_output:
					self.ch.add_message_object('assistant', commands_output)

					arguments = {
						'text': commands_output,
						'stop_event': self.awake_stop_event,
						'sound_stop_event': sound_stop_event
					}
					t = threading.Thread(target=self.csp.speak_tts, args=(arguments,))
					t.start()

					print_text("Module Output (Daisy): ", "red")
					print_text(commands_output, None, "\n")

					response = commands_output

				else:

					try:
						response = self.chat.request(
							messages=messages,
							stop_event=self.awake_stop_event,
							sound_stop_event=sound_stop_event,
							tts=sound
							)
					except Exception as e:
						logging.error("Daisy request error: "+ str(e))
						awake_or_text = self.handle_sleep(sound)
						continue

					if not response:
						logging.error("Daisy request error: No response")
						awake_or_text = self.handle_sleep(sound)
						continue

					self.ch.add_message_object('assistant', response)

				if self.awake_stop_event.is_set():
					awake_or_text = self.handle_sleep(sound)
					continue

				self.led.breathe_color(100, 100, 100)  # Breathe White
			else:
				continue

			continue_conversation = self.chat.request_boolean(
				"The following message is a question, or warrants a response: "+response
				)
			
			if continue_conversation:
				continue
			else:
				awake_or_text = self.handle_sleep(sound)

	def close(self):
		self.daisy_stop_event.set()

	def handle_wake(self):
		if not self.dc_t or not self.dc_t.is_alive():
			self.dc_t = threading.Thread(
				target=listen_for_daisy_cancel, 
				args=(self.daisy_stop_event, self.awake_stop_event)
				)
			self.threads.append(self.dc_t)
			self.dc_t.start()
		
		try:
			# from daisy_llm import ModuleLoader as ml
			hook_instances = self.ml.hook_instances
			if "Daisy_wake" in hook_instances:
				Daisy_wake_instances = hook_instances["Daisy_wake"]
				for instance in Daisy_wake_instances:
					logging.info("Running Daisy_start module: " + type(instance).__name__)
					response_text = instance.main()
		except Exception as e:
			logging.warning("Daisy_wake Hook: " + str(e))


	def handle_sleep(self, sound=None):
		self.awake_stop_event.set()
		self.dc_t.join()
		print_text("\n(∪｡∪)｡｡｡zzz", "pink", "\n\n")
		if sound:
			self.sounds.play_sound_with_thread('end')

		return None
		#thread = threading.Thread(target=self.ch.update_conversation_name_summary, args=())
		#thread.start()
