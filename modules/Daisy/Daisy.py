import logging
import threading
from daisy_llm import ChatSpeechProcessor, ConnectionStatus, SoundManager, Chat, LoadTts
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

		self.daisy_stop_event = threading.Event()
		self.awake_stop_event = threading.Event()

		self.internet_warning_logged = False

	def close(self):
		self.daisy_stop_event.set()


	def main(self, ml=None, ch=None):
		self.sounds.play_sound("beep", 0.5)
		print_text("🌼 DAISY - Voice Assistant 🌼", "pink", "\n")

		self.chat = Chat(ml, ch)

		threads = []
		# Create the TtsThread instance and start it in time for when its needed
		t = LoadTts(self, ml)
		threads.append(t)
		t.start()

		#Check for Internet connection
		self.awake_stop_event.clear()
		t = threading.Thread(target=self.cs.check_internet, args=(self.daisy_stop_event, self.awake_stop_event))
		threads.append(t)
		t.start()

		while not self.daisy_stop_event.is_set():

			awake = False

			self.led.turn_on_color(0, 100, 0)  # Solid Green

			awake = listen_for_daisy_wake(self.daisy_stop_event, self.awake_stop_event)

			self.led.breathe_color(100, 100, 100)  # Breathe Blue
			self.ch.load_context()

			if awake:
				#Check for "Daisy Cancel" sleep word
				dc_t = threading.Thread(target=listen_for_daisy_cancel, args=(self.daisy_stop_event, self.awake_stop_event))
				threads.append(dc_t)
				dc_t.start()

				#HOOK: Daisy_wake
				try:
					from daisy_llm import ModuleLoader as ml
					hook_instances = self.ml.hook_instances
					if "Daisy_wake" in hook_instances:
						Daisy_wake_instances = hook_instances["Daisy_wake"]
						for instance in Daisy_wake_instances:
							logging.info("Running Daisy_start module: "+type(instance).__name__)
							response_text = instance.main()
				except Exception as e:
					logging.warning("Daisy_wake Hook: "+str(e))

				while not self.daisy_stop_event.is_set() and not self.awake_stop_event.is_set():
					if not self.awake_stop_event.is_set():
						self.led.breathe_color(0, 0, 100)  # Breathe Blue
						stt_text = self.csp.stt(self.awake_stop_event, 30, 'alert') #30s timeout

						if self.awake_stop_event.is_set():
							break

						if stt_text and not self.awake_stop_event.is_set():
							self.led.breathe_color(100,0,100)  # Breathe Blue #NEEDS CANCEL LOOP

							self.ch.add_message_object('user', stt_text)

							if self.awake_stop_event.is_set():
								break

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
								logging.error("Daisy request error: "+ e)
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

					else:
						break

				dc_t.join()
				self.sounds.play_sound_with_thread('end', 1.0)

				#Start a thread that will run every minute
				thread = threading.Thread(target=self.ch.update_conversation_name_summary, args=())
				thread.start()

		for t in threads:
			t.join()


