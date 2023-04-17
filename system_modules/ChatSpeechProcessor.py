#import speech_recognition as sr
import pyaudio
import websockets
import asyncio
import base64
import json
import threading
import time
import re
import string
from dotenv import load_dotenv
import pyttsx3
import requests
import logging
import yaml
import nltk.data
import queue
import threading
import time
import queue
import requests
from concurrent.futures import ThreadPoolExecutor

import system_modules.SoundManager as sm
import modules.RgbLed as led



class ChatSpeechProcessor:
	description = "A class that handles speech recognition and text-to-speech processing for a chatbot."

	def __init__(self):
		# Set up AssemblyAI API key and websocket endpoint
		self.uri = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

		load_dotenv()

		# Define global variables
		with open("configs.yaml", "r") as f:
			configs = yaml.safe_load(f)
		self.assembly_ai_api_key = configs["keys"]["assembly_ai"]
		self.tts_speed = 1.0

		self.result_str = ""
		self.new_result_str = ""
		self.result_received = False
		self.sounds = sm.SoundManager('sounds/')
		#self.r = sr.Recognizer()
		self.engine = pyttsx3.init()
		#self.engine.getProperty('voices')
		#self.engine.setProperty('voice', "english-us")
		self.led = led.RgbLed()
		self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

		self.tts_queue = queue.Queue()  # create a queue to hold the tts_sounds
		self.tts_queue_complete = [False]	# use a list to make response_complete mutable

		self.threads = []  # keep track of all threads created


	def queue_and_tts_sentences(self, tts, sentences, sentence_queue_canceled, sentence_queue_complete, stop_event, sound_stop_event=None):

		with ThreadPoolExecutor(max_workers=2) as executor:
			executor.submit(self.queue_tts_from_sentences, tts, sentences, sentence_queue_complete, sentence_queue_canceled, self.tts_queue_complete, self.tts_queue, stop_event)
			executor.submit(self.play_tts_queue, self.tts_queue, sentence_queue_canceled, sentence_queue_complete, self.tts_queue_complete, stop_event, sound_stop_event)
		return
		  
	def queue_tts_from_sentences(self, tts, sentences, sentence_queue_complete, sentence_queue_canceled, tts_queue_complete, tts_queue, stop_event):
		tts_queue_complete[0] = False
		sentences_length = 1

		def queue_tts_items(index):
			queued_sentence = temp_sentences[index]
			logging.info("Queued sentence: " + queued_sentence)

			try:
				tts_queue.put(tts.create_tts_audio(queued_sentence))
			except requests.exceptions.HTTPError as e:
				#self.csp.tts("HTTP Error. Error creating TTS audio. Please check your TTS account.")
				logging.error(f"HTTP Error: {e}")
			except requests.exceptions.ConnectionError as e:
				#self.csp.tts("Connection Error. Error creating TTS audio. Please check your TTS account.")
				logging.error(f"Connection Error: {e}")


		while not stop_event.is_set():
			temp_sentences = sentences[0]
			index = 0

			if not sentences[0]:
				continue

			if len(temp_sentences) > sentences_length:
				logging.debug("Sentences: " + str(sentences))
				sentence_length_difference = len(temp_sentences) - sentences_length

				sentences_length = len(temp_sentences)
				


				for i in range(sentence_length_difference):
					if not sentence_queue_canceled[0]:
						index = (sentence_length_difference-i+1) * -1
						queue_tts_items(index)

			elif sentence_queue_complete[0]:

				#Play a single sentence response
				if len(sentences[0]) == 1:
					logging.info("Single sentence response")
					queued_sentence = sentences[0][0]
					logging.info("Queued sentence: "+queued_sentence)

					try:
						if not sentence_queue_canceled[0]:
							tts_queue.put(tts.create_tts_audio(queued_sentence))
					except requests.exceptions.HTTPError as e:
						#self.csp.tts("HTTP Error. Error creating TTS audio. Please check your TTS account.")
						logging.error(f"HTTP Error: {e}")

					tts_queue_complete[0] = True
					logging.info("TTS queue complete: single sentence response")
					return

				#Play the very last sentence
				elif len(sentences[0]) == len(temp_sentences):
					if len(sentences[0][-1]) == len(temp_sentences[-1]):
							logging.debug("last sentence...")

							queue_tts_items(-1)

							tts_queue_complete[0] = True
							logging.info("TTS queue complete")
							return

				#All tts items used
				if tts_queue.empty():
					tts_queue_complete[0] = True
					logging.info("TTS queue complete")
					return





			if sentence_queue_canceled[0] or stop_event.is_set():
				tts_queue_complete[0] = True
				while not tts_queue.empty(): #Empty out the TTS queue so no sounds linger
					tts_queue.get()
				logging.info("TTS queue canceled")
				return
			time.sleep(0.5) #Wait juuuust a bit to prevent sentence overlap
				

	def play_tts_queue(self, tts_queue, sentence_queue_canceled, sentence_queue_complete, tts_queue_complete, stop_event, sound_stop_event=None):
		tts = []

		# Wait for tts to be generated
		while tts_queue.empty() and not sentence_queue_canceled[0]:
			time.sleep(0.01)

		# Play tts
		while not stop_event.is_set():
			tts = None


			if tts_queue.qsize():
				tts = tts_queue.get(block=True, timeout=0.01)  # get tts from the queue

				#Stop voice assistant "waiting" sound
				if sound_stop_event:
					sound_stop_event.set()
			
				if tts:
					
					# Define global variables
					with open("configs.yaml", "r") as f:
						configs = yaml.safe_load(f)
						self.tts_speed = configs["TTS"]["speed"]
					self.sounds.play_sound(tts, 1.0, stop_event, None, self.tts_speed)
			elif tts_queue_complete[0]:
				logging.info("TTS play queue complete")
				return


	async def stt_send_receive(self, stop_event, timeout_seconds=0, sound = None):
		"""Sends audio data to AssemblyAI STT API and receives text transcription in real time using websockets."""

		self.result_str = ""
		self.new_result_str = ""
		self.result_received = False

		# Set up PyAudio
		FRAMES_PER_BUFFER = 3200
		FORMAT = pyaudio.paInt16
		CHANNELS = 1
		RATE = 16000
		p = pyaudio.PyAudio()
		stream = p.open(
			format=FORMAT,
			channels=CHANNELS,
			rate=RATE,
			input=True,
			frames_per_buffer=FRAMES_PER_BUFFER
		)

		try:
			async with websockets.connect(
				self.uri,
				extra_headers=(("Authorization", self.assembly_ai_api_key),),
				ping_interval=5,
				ping_timeout=20
			) as _ws:
				await asyncio.sleep(0.1)
				logging.info("Receiving SessionBegins ...")
				session_begins = await _ws.recv()
				logging.info(session_begins)
				logging.info("AAI Listening ...")

				async def timeout():
					start_time = time.time()
					elapsed_time = 0

					while not self.result_received and not stop_event.is_set():
						elapsed_time = time.time() - start_time
						if stop_event.is_set():
							logging.info("Timeout()")
							break
						if timeout_seconds > 0: # If timeout is 0s, then dont timeout
							if elapsed_time > timeout_seconds:
								logging.info("Timeout reached")
								stop_event.set()
								return
						await asyncio.sleep(0.01)

					logging.info("timeout(): Timeout cancelled or result received")
					print("Result received: " + str(self.result_received))
					print("Stop event: " + str(stop_event.is_set()))

					return


				async def send():
					logging.info("STT Send start")

					while not self.result_received and not stop_event.is_set():
						if stop_event.is_set():
							logging.info("Send(): Cancelled")
							break

						try:
							data = stream.read(FRAMES_PER_BUFFER)
							data = base64.b64encode(data).decode("utf-8")
							json_data = json.dumps({
								"audio_data":str(data), 
								"punctuate": False, 
								"format_text": False
								})
							await _ws.send(json_data)
						except websockets.exceptions.ConnectionClosedError as e:
							logging.error(f"Connection closed with error code {e.code}: {e.reason}")
							break
						except Exception as e:
							logging.exception(f"Unexpected error: {e}")
							break
						await asyncio.sleep(0.01)

					logging.info("send(): STT Send done")
					return
							
				
				async def receive():
					logging.info("STT Receive start")

					while not self.result_received and not stop_event.is_set():
						if stop_event.is_set():
							logging.info("receive(): Cancelled")
							self.result_str = False
							self.result_received = True
							break

						try:
							self.new_result = await asyncio.wait_for(_ws.recv(), timeout=2) #Timeout if connection is lost
							self.result_str_obj = json.loads(self.new_result)

							logging.info("You: "+str(self.result_str_obj['text']))
							self.led.turn_on_color_random_brightness(0, 0, 100)  # Random brightness Blue

							# If the message type is FinalTranscript, then we are done
							if self.result_str_obj['message_type'] == "FinalTranscript" and self.result_str_obj['text'] != "":
								#DONE
								logging.info("receive(): STT Receive done")
								logging.info("receive(): You said: "+str(self.result_str_obj['text']))

								self.result_str = self.result_str_obj['text']
								self.result_received = True

						except asyncio.TimeoutError:
							logging.warning("receive(): Receive timed out")
							self.result_str = False
							self.result_received = True
						except websockets.exceptions.ConnectionClosedError as e:
							logging.error(f"Connection closed with error code {e.code}: {e.reason}")
							self.result_str = False
							self.result_received = True
						except Exception as e:
							logging.exception(f"Unexpected error: {e}")
							self.result_str = False
							self.result_received = True
					logging.info("receive(): STT Receive done")
					return



				#Play start sound
				if sound:
					self.sounds.play_sound_with_thread(sound)

				send_result, receive_result, timeout_result = await asyncio.gather(
					asyncio.shield(timeout()), asyncio.shield(send()), asyncio.shield(receive())
				)
		except websockets.exceptions.ConnectionClosedError as e:
			logging.error(f"Connection closed with error code {e.code}: {e.reason}")
			self.result_str = False
			self.result_received = True


	def stt(self, stop_event, timeout_seconds=0, sound = None):
		"""Calls stt_send_receive in a new thread and returns the final transcription."""
		# Create an event object to signal the thread to stop
		stt_stop_event = threading.Event()

		def watch_results():
			#global result_received
			#global result_str
			while not stt_stop_event.is_set() and not stop_event.is_set():
				if self.result_received:
					logging.info("Result received: %s", self.result_str)
					self.result_received = False

					# Set the event to signal the thread to stop
					stt_stop_event.set()

				time.sleep(0.1)

			# Join the thread to wait for it to finish
			logging.debug("Joining STT thread...")
			thread.join()
			logging.debug("STT Thread stopped")

			return self.result_str


		# Set up AssemblyAI stt_send_receive loop
		#This is a thread in a thread. I think it can be reduced.
		def start_stt_send_receive():
			asyncio.run(self.stt_send_receive(stop_event, timeout_seconds, sound))

		# Create and start the stt_send_receive thread
		thread = threading.Thread(target=start_stt_send_receive)
		thread.start()

		# Start watching results in the main thread
		result_str = watch_results()

		return result_str

	def remove_non_alphanumeric(self, text):
		"""Removes all characters that are not alphanumeric or punctuation."""

		# Create a set of all valid characters
		valid_chars = set(string.ascii_letters + string.digits + "!()',./?+=-_#$%&*@" + ' ')

		# Use a generator expression to filter out any invalid characters
		filtered_text = ''.join(filter(lambda x: x in valid_chars, text))

		# Log the input and output text at the DEBUG level
		logging.debug(f'Removing non-alphanumeric characters from text: {text}')
		logging.debug(f'Filtered text: {filtered_text}')

		return filtered_text

	def remove_non_alpha(self, text):
		"""Removes all non-alphabetic characters (including punctuation and numbers) from a string and returns the modified string in lowercase."""
		if text:
			# Log a debug message with the input string
			logging.debug(f'Removing non-alpha characters from string: {text}')

			# Use regular expression to replace non-alphanumeric characters with empty string
			text = re.sub(r'[^a-zA-Z]+', '', text)

			# Log a debug message with the modified string
			logging.debug(f'Filtered text: {text}')

			# Return the modified string
			return text.lower()
		else:
			return False
		
	def nltk_sentence_tokenize(self, text, language="english"):
		"""Splits a string into sentences using the NLTK sentence tokenizer."""
		# Log a debug message with the input string
		logging.debug(f'Tokenizing string: {text}')

		# Split the string into sentences
		sentences = nltk.sent_tokenize(text, language)

		# Log a debug message with the modified string
		logging.debug(f'Tokenized sentences: {sentences}')

		# Return the modified string
		return sentences

