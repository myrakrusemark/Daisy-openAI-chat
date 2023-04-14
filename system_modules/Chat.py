import openai
import logging
import queue
import nltk.data
import threading
import time
import requests
import yaml

from elevenlabslib import *
import pydub
import pydub.playback
import io


import system_modules.ConnectionStatus as cs
import system_modules.ChatSpeechProcessor as csp
import system_modules.SoundManager as sm
import system_modules.ContextHandlers as ch
import modules.DaisyMethods as dm
#import modules.TTSElevenLabs as tts
import ModuleLoader as ml



class Chat:
	description = "Implements a chatbot using OpenAI's GPT-3 language model and allows for interaction with the user through speech or text."

	def __init__(self):
		self.csp = csp.instance
		self.cs = cs.instance
		self.sounds = sm.instance
		self.ch = ch.instance
		self.dm = dm.instance
		self.hook_instances = ml.instance.hook_instances

		'''
		#HOOK: Tts
		logging.debug(self.hook_instances)
		if "Tts" in self.hook_instances:
			if len(self.hook_instances["Tts"]) > 1:
				logging.warning("Multiple TTS modules found. Only the first one will be used.: "+type(self.hook_instances["Tts"][0]).__name__)
			logging.debug("Importing Tts instance: "+type(instance).__name__)

			self.tts = self.hook_instances["Tts"]
		'''

		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		openai.api_key = self.configs["keys"]["openai"]

	def request(self, messages, stop_event, sound_stop_event=None, tts=None):
		#Handle LLM request. Optionally convert to sentences and queue for tts, if needed.

		#Queues for handling chunks, sentences, and tts sounds
		sentences = [[]]  # create a queue to hold the sentences
		#tts_queue = queue.Queue()  # create a queue to hold the tts_sounds

		#Flags for handling chunks, sentences, and tts sounds
		sentence_queue_canceled = [False]  # use a list to make response_canceled mutable
		sentence_queue_complete = [False]	# use a list to make response_complete mutable
		#tts_queue_complete = [False]	# use a list to make response_complete mutable

		threads = []  # keep track of all threads created
		text_stream = [""]
		return_text = [""]

		try:
			logging.info("Sending request to OpenAI model...")
			response = openai.ChatCompletion.create(
				model='gpt-4',
				messages=messages,
				temperature=1,
				stream=True
			)

			#Check for tool forms (Chat_request_inner)
			#t = threading.Thread(target=self.stream_toolform_checker, args=(text_stream, sentences_queue, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event))
			#t.start()
			#threads.append(t)

			#Handle chunks. Optionally convert to sentences for sentence_queue, if needed.
			t = threading.Thread(target=self.stream_queue_sentences, args=(response, text_stream, sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts))
			t.start()
			threads.append(t)

			if tts:
				self.csp.queue_and_tts_sentences(tts, sentences, sentence_queue_canceled, sentence_queue_complete, stop_event, sound_stop_event)

			while not return_text[0]:
				time.sleep(0.1)  # wait a bit before checking again

			# return response_complete and return_text[0] when return_text is set
			#for thread in threads:
			t.join()

			return return_text[0]
		
		# Handle different types of errors that may occur when sending request to OpenAI model
		except openai.error.InvalidRequestError as e:
			logging.error(f"Invalid Request Error: {e}")
			self.csp.tts("Invalid Request Error. Sorry, I can't talk right now.")
			return False        
		except openai.APIError as e:
			logging.error(f"API Error: {e}")
			self.csp.tts("API Error. Sorry, I can't talk right now.")
			return False
		except openai.error.RateLimitError as e:
			logging.error(f"RateLimitError: {e}")
			self.csp.tts("Rate Limit Error. Sorry, I can't talk right now.")
			return False
		except ValueError as e:
			logging.error(f"Value Error: {e}")
			self.csp.tts("Value Error. Sorry, I can't talk right now.")
			return False    
		except TypeError as e:
			logging.error(f"Type Error: {e}")
			self.csp.tts("Type Error. Sorry, I can't talk right now.")
			return False  

	def toolform_checker(self, text_stream, sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts=None):
		logging.debug("Checking for tool forms...")

		#HOOK: Chat_request_inner
		#Right now, only one hook can be run at a time. If a hook returns a value, the rest of the hooks are skipped.
		#I may update this soon to allow for inline responses (For example: "5+5 is [Calculator: 5+5]")
		logging.debug(self.hook_instances)
		import ModuleLoader as ml
		if "Chat_request_inner" in self.hook_instances:
			for instance in self.hook_instances["Chat_request_inner"]:
				logging.debug("Running Chat_request_inner module: "+type(instance).__name__)

				tool_found = instance.check(text_stream)

				if tool_found:
					logging.info("Found tool form.")
					#Cancel and clear-out current request
					#sentences[0].append(["END OF STREAM"])
					sentence_queue_canceled[0] = True

					hook_text = instance.main(text_stream, stop_event)

					text_stream = ""

					logging.debug("Hook text: "+hook_text)
					if hook_text:
						
						self.ch.add_message_object('system', hook_text)

						import system_modules.Chat as chat
						tool_chat = chat.Chat()
						response = tool_chat.request(self.ch.get_context_without_timestamp(), stop_event, sound_stop_event, tts)
						tool_chat = None

						return response
					else:
						return False
		return False


	def stream_queue_sentences(self, response, text_stream, sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts=None):
		sentence_queue_complete[0] = False
		sentence_queue_canceled[0] = False
		collected_chunks = []
		collected_messages = []
		text = ""

		tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

		for chunk in response:
			if not sentence_queue_canceled[0]:
				if not stop_event.is_set():
					temp_sentences = []
					collected_chunks.append(chunk)
					chunk_message = chunk['choices'][0]['delta']
					collected_messages.append(chunk_message)
					text_stream[0] = ''.join([m.get('content', '') for m in collected_messages])
					logging.debug(text_stream[0])


					#Check for tool forms every 10 iterations to prevent slowdown
					logging.debug("Checking for tool forms...")

					response = self.toolform_checker(text_stream[0], sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts)
					if response:
						sentence_queue_complete[0] = True
						return_text[0] = response
						logging.info("Sentence queue complete by found toolform")
						return
					
					#Tokenize the text into sentences
					temp_sentences = self.csp.nltk_sentence_tokenize(text_stream[0])
					sentences[0] = temp_sentences  # put the sentences into the queue


		
		#sentences[0].append("END OF STREAM")
		time.sleep(0.01)
		sentence_queue_complete[0] = True
		return_text[0] = text_stream[0]
		logging.info("Sentence queue complete")
		return


	def display_messages(self):
		"""Displays the messages stored in the messages attribute of ContectHandlers."""
		for message in self.ch.messages:
			# Check if the message role is in the list of roles to display
			print(f"{message['role'].upper()}: {message['content']}\n\n")

with open("configs.yaml", "r") as f:
	configs = yaml.safe_load(f)

instance = Chat()
