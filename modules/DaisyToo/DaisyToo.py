import logging
import threading
import time
from daisy_llm import ContextHandlers, ChatSpeechProcessor, ConnectionStatus, SoundManager, Chat, LoadTts
from daisy_llm.Text import print_text
from modules.Daisy.DaisyMethods import listen_for_daisy_wake, listen_for_daisy_cancel
import modules.RgbLed as led

class Daisy:
	description = "Provides a user flow for Chat"
	module_hook = "Main_start"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.chat = Chat(self.ml, self.ch)
		self.csp = ChatSpeechProcessor()
		self.cs = ConnectionStatus()
		self.sounds = SoundManager()
		self.led = led.RgbLed()
		self.tts = None

		self.threads = []
		self.daisy_stop_event = threading.Event()
		self.awake_stop_event = threading.Event()
		self.dc_t = threading.Event()

		self.internet_warning_logged = False

		self.iterable_thought_injection = None
		self.iterable_thought_response = None

		self.messaging = {}
		self.messaging['realtime_thought_input'] = []
		self.rt_event_q = self.ml.messaging_system.subscribe("rt_event")


	def main(self):
		self.sounds.play_sound("beep", 0.5)
		print_text("🌼 DAISY - Voice Assistant 🌼", "pink", "\n")

		#self.chat = Chat(ml, ch)
		self.initialize_tts()
		self.check_internet()
		self.iterable_thought()

		self.awake_stop_event.clear()
		while not self.daisy_stop_event.is_set():
			awake = self.wait_for_wake_word()

			if awake:
				self.handle_wake()

				while not self.daisy_stop_event.is_set() and not self.awake_stop_event.is_set():
					if not self.awake_stop_event.is_set():
						self.led.breathe_color(0, 0, 100)  # Breathe Blue

						#Listening
						stt_text = self.csp.stt(self.awake_stop_event, 30, 'alert') #30s timeout

						if self.awake_stop_event.is_set():
							break

						#Thinking / Speaking
						if stt_text and not self.awake_stop_event.is_set():
							self.led.breathe_color(100,0,100)  # Breathe Blue #NEEDS CANCEL LOOP

							self.ch.add_message_object('user', stt_text)
							self.ml.messaging_system.publish("rt_event", stt_text)

							if self.awake_stop_event.is_set():
								break

							sound_stop_event = threading.Event()
							self.sounds.play_sound_with_thread('waiting', 0.2, self.awake_stop_event, sound_stop_event)

							while True:
								print("Waiting for iterable thought response...")
								if self.iterable_thought_response:
									break
								time.sleep(1)

							sound_stop_event.set()

							self.ch.add_message_object('assistant', self.iterable_thought_response)

							if self.awake_stop_event.is_set():
								break

							self.led.breathe_color(100, 100, 100)  # Breathe White
						else:
							self.awake_stop_event.set()
							break

						self.iterable_thought_injection = None
						self.iterable_thought_response = None

					else:
						break

				self.handle_sleep()

	def close(self):
		self.daisy_stop_event.set()

	def initialize_tts(self):
		self.chat = Chat(self.ml, self.ch)
		t = LoadTts(self, self.ml)
		t.start()
		#t.join()

	def check_internet(self):
		self.awake_stop_event.clear()
		t = threading.Thread(target=self.cs.check_internet, args=(self.daisy_stop_event, self.awake_stop_event))
		self.threads.append(t)
		t.start()



	def iterable_thought(self):
		t = threading.Thread(target=self.iterate_thought)
		self.threads.append(t)
		t.start()

	def build_iterable_prompt(self):
		prompt = """1. The previous messages in this context are your own previous thoughts.
2. Please create your next thought.
3. You are only responding to yourself, not a user. No need to be polite.
5. Be creative. Have fun. Be yourself.
5. Do not include any extra text, only your iterated Thoughts.\n\n"""

		print("ADDING RT THOUGHT INPUT: ")
		for message in self.rt_event_q.listen():
			print("MESSAGE: "+message)

		#print_text(message, "blue")
		#self.rt_items.append(message)

		return prompt
	
	def iterate_thought(self):
		iterable_ch = ContextHandlers('iterable_thought.db')
		iterable_ch.load_context()

		while not self.daisy_stop_event.is_set():
			wait_time = 10

			messages = iterable_ch.get_context_without_timestamp()

			prompt = self.build_iterable_prompt()
			print_text("ITERABLE THOUGHT INPUT: ", "blue")
			print_text(prompt, None, "\n\n")

			prompt_message = iterable_ch.single_message_context("user", prompt, incl_timestamp=False)

			messages_to_be_sent = messages
			messages_to_be_sent.append(prompt_message)

			tool_checker_response = self.chat.toolform_checker(messages=messages)
			if tool_checker_response:
				print_text("TOOL CHECKER OUTPUT: ", color="red")
				print_text(tool_checker_response, None, "\n\n")
				iterable_ch.add_message_object('system', tool_checker_response)

			print_text("THOUGHT: ", color="green", style="italic")
			try:
				response = self.chat.request(
					messages=messages_to_be_sent,
					stop_event=self.daisy_stop_event,
					tool_check=False,
					tts=None,
					response_label=False
					)
			except Exception as e:
				logging.error("Daisy request error: "+ e)
				break



			if not response:
				logging.error("Daisy request error: No response")
				break

			if tool_checker_response:
				if "TTS Tool: Spoke aloud:" in tool_checker_response:
					self.messaging['realtime_thought_input'] = []

			iterable_ch.add_message_object('assistant', response)	

			while wait_time > 0 and self.iterable_thought_injection is None:
				time.sleep(1)  # Wait for 1 second
				wait_time -= 1			

	def wait_for_wake_word(self):
		self.led.turn_on_color(0, 100, 0)  # Solid Green
		awake = listen_for_daisy_wake(self.daisy_stop_event, self.awake_stop_event)
		self.led.breathe_color(100, 100, 100)  # Breathe Blue
		return awake

	def handle_wake(self):
		self.dc_t = threading.Thread(target=listen_for_daisy_cancel, args=(self.daisy_stop_event, self.awake_stop_event))
		self.threads.append(self.dc_t)
		self.dc_t.start()
		try:
			from daisy_llm import ModuleLoader as ml
			hook_instances = self.ml.hook_instances
			if "Daisy_wake" in hook_instances:
				Daisy_wake_instances = hook_instances["Daisy_wake"]
				for instance in Daisy_wake_instances:
					logging.info("Running Daisy_start module: " + type(instance).__name__)
					response_text = instance.main()
		except Exception as e:
			logging.warning("Daisy_wake Hook: " + str(e))

		self.ch.new_conversation()

	def handle_sleep(self):
		self.iterable_thought_injection = None
		self.iterable_thought_response = None
		self.dc_t.join()
		self.sounds.play_sound_with_thread('end', 1.0)
		thread = threading.Thread(target=self.ch.update_conversation_name_summary, args=())
		thread.start()

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

