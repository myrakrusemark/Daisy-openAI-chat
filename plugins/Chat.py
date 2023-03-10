import os
import re
from dotenv import load_dotenv
import colorama
import openai
from plugins import ConnectionStatus
from plugins import constants
import logging
import os
import importlib

from plugins import ChatSpeechProcessor
csp = ChatSpeechProcessor.ChatSpeechProcessor()
cs = ConnectionStatus.ConnectionStatus()

#Initialize available sound effects
from plugins import SoundManager
sounds = SoundManager.SoundManager('sounds/')




class Chat:
	description = "Implements a chatbot using OpenAI's GPT-3 language model and allows for interaction with the user through speech or text."

	def __init__(self, api_key="", messages=[], chat_module_hooks = []):
		self.messages = messages
		self.api_key = api_key

		self.Chat_chat_inner_instances = chat_module_hooks["Chat_chat_inner_instances"]

		#Initialize
		load_dotenv()

	def chat(self):
		"""Engages in conversation with the user by sending and receiving messages from an OpenAI model."""
		while True:
			if cs.check_internet():

				#Get and display recognized text
				print(f"'{constants.sleep_word}' to end")
				#user_input = csp.stt()
				#print("You: "+user_input)

				web_response_text = ""
					
				logging.info("Sending openAI request")
				response_text = self.request()
				
				if response_text:
					#HOOK: Chat_chat_inner
					if self.Chat_chat_inner_instances:
						for instance in self.Chat_chat_inner_instances:
							logging.info("Running Chat_chat_inner plugin: "+type(instance).__name__)
							response_text = instance.main(response_text, self.request)

					return response_text
	   
			continue

	def request(self, context=True, new_message={}):
		"""Sends a request to the OpenAI model and returns the response text."""
		openai.api_key = self.api_key

		try:
			# If audio is enabled, play a sound to indicate waiting for response
			sounds.play_sound_with_thread('waiting', 0.2)


			# Send request to OpenAI model
			response = openai.ChatCompletion.create(
				model="gpt-3.5-turbo",
				messages=self.messages if context else new_message
			)

			# Get response text from OpenAI model
			response_text=response["choices"][0]["message"]["content"]

			# If audio is enabled, stop the waiting sound
			sounds.stop_playing()

			# Return response text
			logging.debug("Response text: "+response_text)
			return response_text
		
		# Handle different types of errors that may occur when sending request to OpenAI model
		except openai.error.InvalidRequestError as e:
			logging.error(f"Invalid Request Error: {e}")
			constants.stop_sound = True
			csp.tts("Invalid Request Error. Sorry, I can't talk right now.")
			return False        
		except openai.APIError as e:
			logging.error(f"API Error: {e}")
			constants.stop_sound = True
			csp.tts("API Error. Sorry, I can't talk right now.")
			return False
		except ValueError as e:
			logging.error(f"Value Error: {e}")
			constants.stop_sound = True
			csp.tts("Value Error. Sorry, I can't talk right now.")
			return False    
		except TypeError as e:
			logging.error(f"Type Error: {e}")
			constants.stop_sound = True
			csp.tts("Type Error. Sorry, I can't talk right now.")
			return False 

	def display_messages(self):
		"""Displays the messages stored in the messages attribute of the Chat object."""
		for message in self.messages:
			# Check if the message role is in the list of roles to display
			print(f"{message['role'].upper()}: {message['content']}\n\n")