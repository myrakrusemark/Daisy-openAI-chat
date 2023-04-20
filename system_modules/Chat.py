import openai
import logging
import nltk.data
import threading
import time
import yaml
import json
import requests

import system_modules.ChatSpeechProcessor as csp
import system_modules.SoundManager as sm



class Chat:
	description = "Implements a chatbot using OpenAI's GPT-3 language model and allows for interaction with the user through speech or text."

	def __init__(self, ml=None, ch=None):
		self.ml = ml
		self.ch = ch
		self.csp = csp.ChatSpeechProcessor()
		self.sounds = sm.SoundManager()

		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		openai.api_key = self.configs["keys"]["openai"]

		nltk.data.load('tokenizers/punkt/english.pickle')

	def request(self, messages, stop_event=None, sound_stop_event=None, tts=None, tool_check=True, model="gpt-3.5-turbo", ):
		#Handle LLM request. Optionally convert to sentences and queue for tts, if needed.

		#Queues for handling chunks, sentences, and tts sounds
		sentences = [[]]  # create a queue to hold the sentences



		if not stop_event:
			stop_event = threading.Event()
		if not sound_stop_event:
			sound_stop_event = threading.Event()

		#Flags for handling chunks, sentences, and tts sounds
		sentence_queue_canceled = [False]  # use a list to make response_canceled mutable
		sentence_queue_complete = [False]	# use a list to make response_complete mutable

		threads = []  # keep track of all threads created
		text_stream = [""]
		return_text = [""]



		if tool_check:
			response = self.toolform_checker(messages, stop_event, sound_stop_event, tts)
			if response:
				messages.append(self.ch.single_message_context("system", response, False))

		try:
			logging.info("Sending request to OpenAI model...")
			response = openai.ChatCompletion.create(
				model=model,
				messages=messages,
				temperature=0.7,
				stream=True,
				request_timeout=2,
			)

			#Handle chunks. Optionally convert to sentences for sentence_queue, if needed.
			t = threading.Thread(target=self.stream_queue_sentences, args=(response, text_stream, sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts))
			t.start()
			threads.append(t)

			if tts:
				self.csp.queue_and_tts_sentences(tts, sentences, sentence_queue_canceled, sentence_queue_complete, stop_event, sound_stop_event)

			while not return_text[0] and not stop_event.is_set():
				time.sleep(0.1)  # wait a bit before checking again

			# return response_complete and return_text[0] when return_text is set
			#for thread in threads:
			t.join()
			return return_text[0]
		
		# Handle different types of errors that may occur when sending request to OpenAI model
		except openai.error.Timeout as e:
			logging.error(f"Timeout: {e}")
			#self.csp.tts("TimeoutError Error. Check your internet connection.")
			return False  
		except openai.error.APIConnectionError as e:
			logging.error(f"APIConnectionError: {e}")
			#self.csp.tts("APIConnectionError. Sorry, I can't talk right now.")
			return False  
		except openai.error.InvalidRequestError as e:
			logging.error(f"Invalid Request Error: {e}")
			#self.csp.tts("Invalid Request Error. Sorry, I can't talk right now.")
			return False        
		except openai.APIError as e:
			logging.error(f"API Error: {e}")
			#self.csp.tts("API Error. Sorry, I can't talk right now.")
			return False
		except openai.error.RateLimitError as e:
			logging.error(f"RateLimitError: {e}")
			#self.csp.tts("Rate Limit Error. Sorry, I can't talk right now.")
			return False
		except ValueError as e:
			logging.error(f"Value Error: {e}")
			#self.csp.tts("Value Error. Sorry, I can't talk right now.")
			return False    
		except TypeError as e:
			logging.error(f"Type Error: {e}")
			#self.csp.tts("Type Error. Sorry, I can't talk right now.")
			return False  

	def toolform_checker(self, messages, stop_event, sound_stop_event, tts=None):
		logging.debug("Checking for tool forms...")

		#HOOK: Chat_request_inner
		#Right now, only one hook can be run at a time. If a hook returns a value, the rest of the hooks are skipped.
		#I may update this soon to allow for inline responses (For example: "5+5 is [Calculator: 5+5]")
		if self.ml:
			hook_instances = self.ml.get_hook_instances()
			logging.debug(hook_instances)

			if "Chat_request_inner" in hook_instances:

				#Create a tool-chooser prompt
				prompt = """1. "Tools" contains a list of available tools for you to use.
2. Choose one, or more, or None of the tools that are most useful given the context of the "Conversation".
4. Format your response using JSON, like this: [{"name":"tool_form_name", "arg":"tool_form_argument"}]
5. If you choose more than one tool, create an list. Like this: [{"name":"tool_form_name", "arg":"tool_form_argument"}, {"name":"tool_form_name", "arg":"tool_form_argument"}]
6. If you choose no tools, respond with ["None"].
7. Your response will be parsed in a computer program. Do not include any additional text in your response.
8. "Conversation" starts with the earliest message and ends with the most recent message.
9. If the latest message changes the subject of the conversation, even if an earlier message is still relevant, you may respond with ["None"].

Tools:
"""
				#Add all available tools to the prompt
				for module in self.ml.get_available_modules():
					if "tool_form_name" in module:
						prompt += '{"name":"'
						if "tool_form_name" in module:
							prompt += module["tool_form_name"]+'", "arg":"'
						if "tool_form_argument" in module:
							prompt += module["tool_form_argument"]+'"}\n'
						if "tool_form_description" in module:
							prompt += module["tool_form_description"]+"\n\n"

				#Get the last three messages and add them to the prompt
				prompt += "Conversation:\n"
				last_three_messages = messages[-3:]
				for message in last_three_messages:
					prompt += str(message)+"\n"
				print("PROMPT",prompt)
				message = [{'role': 'system', 'content': prompt}]
				logging.debug(prompt)

				#Send prompt to OpenAI model
				response = self.request(message, stop_event, None, None, False)

				#Parse JSON response
				data = None
				start_index = response.find('[')
				if start_index >= 0:
					end_index = response.find(']', start_index) + 1
					json_data = response[start_index:end_index]
					try:
						data = json.loads(json_data)
					except json.decoder.JSONDecodeError as e:
						print("JSONDecodeError: "+str(e))
						data = None
					if data and data[0] == "None":
						data = None
				else:
					logging.warning("No JSON data found in string.")

				logging.info("Tool form chosen: "+str(data))
				
				prompt = ""
				if data:
					for d in data:
						for module in self.ml.get_available_modules():
							if "tool_form_name" in module:
								if module["tool_form_name"] == d["name"]:
									logging.info("Tool form found: "+module["tool_form_name"])
									class_name = module["class_name"]
									chat_request_inner_hook_instances = self.ml.get_hook_instances()["Chat_request_inner"]
									for instance in chat_request_inner_hook_instances:
										if instance.__class__.__name__ == class_name.split(".")[-1]:
											logging.info("Found instance: "+instance.__class__.__name__)
											result = instance.main(d['arg'], stop_event)

											prompt += """Below is the response from the tool: """+module["tool_form_name"]+". Use it to continue the conversation.\n"
											prompt += result + "\n\n"
											print("PROMPT",prompt)

				if prompt:
					return prompt
				else:
					logging.warning("No data found.")
					return False

		return False


	def stream_queue_sentences(self, response, text_stream, sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts=None):
		sentence_queue_complete[0] = False
		sentence_queue_canceled[0] = False
		collected_chunks = []
		collected_messages = []

		try:
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
						#logging.debug("Checking for tool forms...")

						#response = self.toolform_checker(text_stream[0], sentences, sentence_queue_canceled, sentence_queue_complete, return_text, stop_event, sound_stop_event, tts)
						#if response:
						#	sentence_queue_complete[0] = True
						#	return_text[0] = response
						#	logging.info("Sentence queue complete by found toolform")
						#	return
						
						#Tokenize the text into sentences
						temp_sentences = self.csp.nltk_sentence_tokenize(text_stream[0])
						sentences[0] = temp_sentences  # put the sentences into the queue
					else:
						sentence_queue_canceled[0] = True
						logging.info("Sentence queue canceled")
						return
		except requests.exceptions.ConnectionError as e:
			logging.error("stream_queue_sentences(): Request timeout. Check your internet connection.")
			sentence_queue_canceled[0] = True


		time.sleep(0.01)
		sentence_queue_complete[0] = True
		return_text[0] = text_stream[0]
		sound_stop_event.set()
		logging.info("Sentence queue complete")
		return


	def display_messages(self, chat_handlers):
		"""Displays the messages stored in the messages attribute of ContectHandlers."""
		for message in chat_handlers.get_context():
			# Check if the message role is in the list of roles to display
			print(f"{message['role'].upper()}: {message['content']}\n\n")

