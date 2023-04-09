import os
import re
from dotenv import load_dotenv
import openai
import logging
import os
import importlib
from modules import constants
import queue
import nltk.data
import threading
import time



import modules.ConnectionStatus as cs
import modules.ChatSpeechProcessor as csp
import modules.SoundManager as sm
import modules.ContextHandlers as ch
import modules.DaisyMethods as dm
import ModuleLoader as ml



class Chat:
	description = "Implements a chatbot using OpenAI's GPT-3 language model and allows for interaction with the user through speech or text."

	#def __init__(self, api_key="", chat_module_hooks = []):
	def __init__(self, api_key=""):

		openai.api_key = api_key

		self.csp = csp.instance
		self.cs = cs.instance
		self.sounds = sm.instance
		self.ch = ch.instance
		self.dm = dm.instance
		
		
	def chat(self, messages, stop_event):
		"""Engages in conversation with the user by sending and receiving messages from an OpenAI model."""
		if self.cs.check_internet():
				
			logging.info("Sending openAI request")

			response_text = self.request(messages, stop_event)
			
			if response_text:
				#HOOK: Chat_chat_inner
				hook_instances = ml.instance.hook_instances
				print(hook_instances)
				if "Chat_chat_inner" in hook_instances:
					Chat_chat_inner_instances = hook_instances["Chat_chat_inner"]
					for instance in Chat_chat_inner_instances:
						logging.info("Running Chat_chat_inner module: "+type(instance).__name__)
						response_text = instance.main(response_text)

				return response_text
	

	def request(self, messages, stop_event):
		sentences_queue = queue.Queue()  # create a queue to hold the sentences
		response_complete = [False]  # use a list to make response_complete mutable
		threads = []  # keep track of all threads created
		return_text = [""]

		try:

			response = openai.ChatCompletion.create(
				model='gpt-3.5-turbo',
				messages=messages,
				temperature=0,
				stream=True
			)

			t = threading.Thread(target=self.openai_stream_chunkerize, args=(response, sentences_queue, response_complete, return_text, stop_event))
			t.start()
			threads.append(t)

			t = threading.Thread(target=self.queue_sentences, args=(sentences_queue, response_complete, stop_event), daemon=True)
			t.start()
			threads.append(t)

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

	def openai_stream_chunkerize(self, response, sentences_queue, response_complete, return_text, stop_event):
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
				temp_sentences = tokenizer.tokenize(text)
				sentences_queue.put(temp_sentences)  # put the sentences into the queue
		temp_sentences.append("END OF STREAM")
		sentences_queue.put(temp_sentences)  # put the sentences into the queue
		response_complete[0] = True
		time.sleep(0.01)
		return_text[0] = text
		return

	def queue_sentences(self, sentences_queue, response_complete, stop_event):
		sentences_length = 0
		sentences = []
		while not stop_event.is_set() and not response_complete[0]:
			try:
				sentences = sentences_queue.get(block=True, timeout=0.01)  # get sentences from the queue
			except queue.Empty:
				continue

			if len(sentences) > sentences_length and len(sentences) >= 1:
				sentences_length = len(sentences)
				if len(sentences) >= 2:
					print(sentences[-2])  # print the second-to-last sentence in sentences


	def display_messages(self):
		"""Displays the messages stored in the messages attribute of ContectHandlers."""
		for message in self.ch.messages:
			# Check if the message role is in the list of roles to display
			print(f"{message['role'].upper()}: {message['content']}\n\n")

load_dotenv()
instance = Chat(os.environ["API_KEY"])
