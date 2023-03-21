import os
import re
from dotenv import load_dotenv
import openai
import logging
import os
import importlib
from modules import constants

import modules.ConnectionStatus as cs
import modules.ChatSpeechProcessor as csp
import modules.SoundManager as sm
import modules.ContextHandlers as ch
import ModuleLoader as ml
import modules.DaisyMethods as dm



class Chat:
	description = "Implements a chatbot using OpenAI's GPT-3 language model and allows for interaction with the user through speech or text."

	#def __init__(self, api_key="", chat_module_hooks = []):
	def __init__(self, api_key=""):

		self.api_key = api_key

		self.csp = csp.instance
		self.cs = cs.instance
		self.sounds = sm.instance
		self.ch = ch.instance
		self.messages = self.ch.messages
		self.dm = dm.instance

		
	def chat(self):
		"""Engages in conversation with the user by sending and receiving messages from an OpenAI model."""
		while True:
			if self.cs.check_internet():

				print(f"'{constants.sleep_word}' to end")

				web_response_text = ""
					
				logging.info("Sending openAI request")
				response_text = self.request()
				
				if response_text:
					#HOOK: Chat_chat_inner
					Chat_chat_inner_instances = ml.instance.Chat_chat_inner_instances

					if Chat_chat_inner_instances:
						for instance in Chat_chat_inner_instances:
							logging.info("Running Chat_chat_inner module: "+type(instance).__name__)
							response_text = instance.main(response_text, self.request)

					return response_text
	   
			continue

	def request(self, context=True, new_message={}):
	    """Sends a request to the OpenAI model and returns the response text."""
	    openai.api_key = self.api_key

	    try:
	        # If audio is enabled, play a sound to indicate waiting for response
	        self.sounds.play_sound_with_thread('waiting', 0.2)

	        # Introduce a loop that checks for the cancel flag
	        while not self.dm.get_cancel_loop():
	            # Send request to OpenAI model
	            response = openai.ChatCompletion.create(
	                model="gpt-4",
	                messages=self.messages if context else new_message
	            )

	            # Get response text from OpenAI model
	            response_text=response["choices"][0]["message"]["content"]

	            # If audio is enabled, stop the waiting sound
	            self.sounds.stop_playing()

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
