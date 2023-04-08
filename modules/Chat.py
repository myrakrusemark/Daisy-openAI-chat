import os
import re
from dotenv import load_dotenv
import openai
import logging
import os
import importlib

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

		self.api_key = api_key

		self.csp = csp.instance
		self.cs = cs.instance
		self.sounds = sm.instance
		self.ch = ch.instance
		self.dm = dm.instance

		
	def chat(self, context):
		"""Engages in conversation with the user by sending and receiving messages from an OpenAI model."""
		if self.cs.check_internet():
				
			logging.info("Sending openAI request")

			#Someday this should be a hook to switch out LLMs
			response_text = self.request(context)
			
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
	

	def request(self, context):
		"""Sends a request to the OpenAI model and returns the response text."""
		openai.api_key = self.api_key

		try:
			# Introduce a loop that checks for the cancel flag
			while not self.dm.get_cancel_loop():
				# Send request to OpenAI model
				response = openai.ChatCompletion.create(
					model="gpt-4",
					messages=context
				)

				# Get response text from OpenAI model
				response_text=response["choices"][0]["message"]["content"]

				# Return response text
				logging.debug("Response text: "+response_text)
				return response_text

			# If the cancel flag is set, break out of the loop
			logging.info("Request cancelled")
			return None

		# Handle different types of errors that may occur when sending request to OpenAI model
		except openai.error.InvalidRequestError as e:
			logging.error(f"Invalid Request Error: {e}")
			constants.stop_sound = True
			self.csp.tts("Invalid Request Error. Sorry, I can't talk right now.")
			return False        
		except openai.APIError as e:
			logging.error(f"API Error: {e}")
			constants.stop_sound = True
			self.csp.tts("API Error. Sorry, I can't talk right now.")
			return False
		except openai.error.RateLimitError as e:
			logging.error(f"API Error: {e}")
			constants.stop_sound = True
			self.csp.tts("Rate Limit Error. Sorry, I can't talk right now.")
			return False
		except ValueError as e:
			logging.error(f"Value Error: {e}")
			constants.stop_sound = True
			self.csp.tts("Value Error. Sorry, I can't talk right now.")
			return False    
		except TypeError as e:
			logging.error(f"Type Error: {e}")
			constants.stop_sound = True
			self.csp.tts("Type Error. Sorry, I can't talk right now.")
			return False 



	def display_messages(self):
		"""Displays the messages stored in the messages attribute of ContectHandlers."""
		for message in self.ch.messages:
			# Check if the message role is in the list of roles to display
			print(f"{message['role'].upper()}: {message['content']}\n\n")

load_dotenv()
instance = Chat(os.environ["API_KEY"])
