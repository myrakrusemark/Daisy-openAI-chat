import logging
import threading
import time
import queue

import daisy_llm.ChatSpeechProcessor as csp
import daisy_llm.ConnectionStatus as cs
import daisy_llm.SoundManager as sm
import daisy_llm.Chat as chat
import daisy_llm.LoadTts as tts

from daisy_llm.Text import print_text

from modules.Daisy.DaisyMethods import listen_for_daisy_wake, listen_for_daisy_cancel
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
		self.csp = csp.ChatSpeechProcessor()
		self.cs = cs.ConnectionStatus()
		self.sounds = sm.SoundManager()
		self.led = led.RgbLed()
		self.tts = None

		self.threads = []
		self.daisy_stop_event = threading.Event()
		self.awake_stop_event = threading.Event()
		self.dc_t = threading.Event()

		self.internet_warning_logged = False

		#Handle global text input
		self.text_input_thread = None
		self.text_input_result = None

	def main(self):
		self.sounds.play_sound("beep", 0.5)
		print_text("🌼 DAISY - Voice Assistant 🌼", "pink", "\n")

		self.chat = chat.Chat(self.ml)
		self.initialize_tts()
		self.check_internet()

		self.awake_stop_event.clear()

		#self.start_text_input_thread()

		self.ch.load_context()

		while not self.daisy_stop_event.is_set():

			#Wait for wake word or get input from the keyboard
			self.awake_stop_event.clear()
			awake_or_text = self.wait_for_wake_word_or_input()

			self.handle_wake()
			self.led.breathe_color(0, 0, 100)  # Breathe Blue

			#Get input
			sound = self.tts
			if type(awake_or_text) == bool:
				input_text = self.csp.stt(self.awake_stop_event, 30, 'alert') #30s timeout
			elif type(awake_or_text) == str:
				input_text = awake_or_text
				sound = None

			if self.awake_stop_event.is_set():
				break

			if input_text and not self.awake_stop_event.is_set():
				self.led.breathe_color(100,0,100)  # Breathe Blue #NEEDS CANCEL LOOP

				self.ch.add_message_object('user', input_text)

				if self.awake_stop_event.is_set():
					break

				sound_stop_event = threading.Event()
				if sound:
					self.sounds.play_sound_with_thread('waiting', 0.2, self.awake_stop_event, sound_stop_event)

				#Determine and run commands
				commands_output = "None"
				messages = self.ch.get_context(include_timestamp=False, include_system=False)

				try:
					commands_output = self.chat.determine_and_run_commands(messages=self.ch.get_context_without_timestamp(), tts=self.tts)
				except Exception as e:
					logging.error("determine_and_run_commands error: "+ str(e))

				if commands_output:
					commands_output_message = self.ch.single_message_context('user', commands_output, incl_timestamp=False)
					messages.append(commands_output_message)
					print_text("Module Output (Daisy): ", "red")
					print_text(commands_output, None, "\n")

				#Get LLM response
				try:
					text = self.chat.request(
						messages=messages,
						model="gpt-4",
						stop_event=self.awake_stop_event,
						sound_stop_event=sound_stop_event,
						tts=sound
						)
				except Exception as e:
					logging.error("Daisy request error: "+ str(e))
					self.awake_stop_event.set()
					break

				if not text:
					logging.error("Daisy request error: No response")
					self.awake_stop_event.set()
					break

				self.ch.add_message_object('assistant', text)

				if self.awake_stop_event.is_set():
					break

				self.led.breathe_color(100, 100, 100)  # Breathe White
			else:
				self.awake_stop_event.set()
				break

			self.awake_stop_event.set()
			self.handle_sleep(sound)

	def close(self):
		self.daisy_stop_event.set()

	def initialize_tts(self):
		t = tts.LoadTts(self, self.ml)
		t.start()
		t.join()

	def check_internet(self):
		self.awake_stop_event.clear()
		t = threading.Thread(target=self.cs.check_internet, args=(self.daisy_stop_event, self.awake_stop_event))
		self.threads.append(t)
		t.start()		

	def wait_for_wake_word_or_input(self):
		self.led.turn_on_color(0, 100, 0)  # Solid Green
		awake = [False]
		stop_event = threading.Event()

		# Listen for wake word
		def listen_for_wake_word():
			awake[0] = listen_for_daisy_wake(self.daisy_stop_event, stop_event)

		# Start the wake word thread
		lw_t = threading.Thread(target=listen_for_wake_word, args=())
		lw_t.start()

		# Check for new inputs and wake word
		print_text("Type text or say the wake word: ", "green")
		while lw_t.is_alive():
			new_input = self.im.get_input()
			if new_input is not None:
				# Stop the wake word thread and return the new input
				stop_event.set()
				lw_t.join()
				self.led.breathe_color(100, 100, 100)  # Breathe Blue
				print_text("٩(ˊ〇ˋ*)و", "pink", "\n")
				return new_input
			elif awake[0]:
				# Return True if the wake word is detected
				return True

		self.led.breathe_color(100, 100, 100)  # Breathe Blue
		print_text("٩(ˊ〇ˋ*)و", "pink", "\n")

		# Return None if no input was received and no wake word was detected
		return None


	def handle_wake(self):
		self.dc_t = threading.Thread(target=listen_for_daisy_cancel, args=(self.daisy_stop_event, self.awake_stop_event))
		self.threads.append(self.dc_t)
		self.dc_t.start()
		try:
			#from daisy_llm import ModuleLoader as ml
			hook_instances = self.ml.hook_instances
			if "Daisy_wake" in hook_instances:
				Daisy_wake_instances = hook_instances["Daisy_wake"]
				for instance in Daisy_wake_instances:
					logging.info("Running Daisy_start module: " + type(instance).__name__)
					response_text = instance.main()
		except Exception as e:
			logging.warning("Daisy_wake Hook: " + str(e))


	def handle_sleep(self, sound):
		self.dc_t.join()
		if sound:
			self.sounds.play_sound_with_thread('end', 1.0)
		#thread = threading.Thread(target=self.ch.update_conversation_name_summary, args=())
		#thread.start()

	def handle_user_input(self):
		self.led.breathe_color(0, 0, 100)  # Breathe Blue
		stt_text = self.csp.stt(self.awake_stop_event, 30, 'alert')  # 30s timeout
		if self.awake_stop_event.is_set():
			return None
		if stt_text and not self.awake_stop_event.is_set():
			self.led.breathe_color(100, 0, 100)  # Breathe Blue #NEEDS CANCEL LOOP
			self.ch.add_message_object('user', stt_text)
			if self.awake_stop_event.is_set():
				return None
			sound_stop_event = threading.Event()
			self.sounds.play_sound_with_thread('waiting', 0.2, self.awake_stop_event, sound_stop_event)

			try:
				text = self.chat.request(
					messages=self.ch.get_context_without_timestamp(),
					stop_event=self.awake_stop_event,
					sound_stop_event=sound_stop_event,
					tool_check=True,
					tts=self.tts
				)
			except Exception as e:
				logging.error("Daisy request error: " + str(e))
				self.awake_stop_event.set()
				return None

			if not text:
				logging.error("Daisy request error: No response")
				self.awake_stop_event.set()
				return None

			self.ch.add_message_object('assistant', text)

			if self.awake_stop_event.is_set():
				return None

			self.led.breathe_color(100, 100, 100)  # Breathe White

			return text




