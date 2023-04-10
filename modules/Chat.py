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


import modules.ConnectionStatus as cs
import modules.ChatSpeechProcessor as csp
import modules.SoundManager as sm
import modules.ContextHandlers as ch
import modules.DaisyMethods as dm
import modules.TTSElevenLabs as tts
import ModuleLoader as ml



class Chat:
	description = "Implements a chatbot using OpenAI's GPT-3 language model and allows for interaction with the user through speech or text."

	def __init__(self):
		self.csp = csp.instance
		self.cs = cs.instance
		self.sounds = sm.instance
		self.ch = ch.instance
		self.dm = dm.instance
		self.tts = tts.TtsElevenLabs()

		self.hook_instances = ml.instance.hook_instances

		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		openai.api_key = self.configs["keys"]["openai"]

	def request(self, messages, stop_event, sound_stop_event=None, tts=False):
		#Handle LLM request. Optionally convert to sentences and queue for tts, if needed.

		#Queues for handling chunks, sentences, and tts sounds
		sentences_queue = queue.Queue()  # create a queue to hold the sentences
		#tts_queue = queue.Queue()  # create a queue to hold the tts_sounds

		#Flags for handling chunks, sentences, and tts sounds
		sentence_queue_canceled = [False]  # use a list to make response_canceled mutable
		sentence_queue_complete = [False]	# use a list to make response_complete mutable
		#tts_queue_complete = [False]	# use a list to make response_complete mutable

		threads = []  # keep track of all threads created
		return_text = [""]

		try:
			logging.info("Sending request to OpenAI model...")
			response = openai.ChatCompletion.create(
				model='gpt-3.5-turbo',
				messages=messages,
				temperature=0,
				stream=True
			)

			#Handle chunks. Optionally convert to sentences for sentence_queue, if needed.
			t = threading.Thread(target=self.openai_stream_queue_sentences, args=(response, sentences_queue, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event))
			t.start()
			threads.append(t)

			if tts:
				self.csp.queue_and_tts_sentences(sentences_queue, sentence_queue_canceled, sentence_queue_complete, stop_event, sound_stop_event)

			while not return_text[0]:
				time.sleep(0.1)  # wait a bit before checking again

			# return response_complete and return_text[0] when return_text is set
			for thread in threads:
				thread.join()
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
			logging.error(f"API Error: {e}")
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

	def openai_stream_queue_sentences(self, response, sentences_queue, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event):
		collected_chunks = []
		collected_messages = []
		text = ""

		tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

		for chunk in response:
			if not stop_event.is_set():
				temp_sentences = []
				collected_chunks.append(chunk)
				chunk_message = chunk['choices'][0]['delta']
				collected_messages.append(chunk_message)
				text = ''.join([m.get('content', '') for m in collected_messages])
				if text:
					#HOOK: Chat_request_inner
					#Right now, only one hook can be run at a time. If a hook returns a value, the rest of the hooks are skipped.
					#I may update this soon to allow for inline responses (For example: "5+5 is [Calculator: 5+5]")
					logging.debug(self.hook_instances)
					if "Chat_request_inner" in self.hook_instances:
						Chat_chat_inner_instances = self.hook_instances["Chat_request_inner"]
						for instance in Chat_chat_inner_instances:
							logging.debug("Running Chat_request_inner module: "+type(instance).__name__)
							hook_text = instance.main(text, stop_event, sound_stop_event)
							if hook_text != False:
								break
						#Empty out text and queues, and return
						if hook_text != False:
							while not sentences_queue.empty():
								sentences_queue.get()
							sentences_queue.put(["END OF STREAM"])
							sentence_queue_canceled[0] = True
							return_text[0] = hook_text
							return
						
				#Tokenize the text into sentences
				temp_sentences = self.csp.nltk_sentence_tokenize(text)

				sentences_queue.put(temp_sentences)  # put the sentences into the queue
		temp_sentences.append("END OF STREAM")
		sentences_queue.put(temp_sentences)  # put the sentences into the queue
		time.sleep(0.01)
		sentence_queue_complete[0] = True
		return_text[0] = text
		return


	def display_messages(self):
		"""Displays the messages stored in the messages attribute of ContectHandlers."""
		for message in self.ch.messages:
			# Check if the message role is in the list of roles to display
			print(f"{message['role'].upper()}: {message['content']}\n\n")

with open("configs.yaml", "r") as f:
	configs = yaml.safe_load(f)

instance = Chat()
