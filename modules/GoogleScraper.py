from dotenv import load_dotenv
import openai
from serpapi import GoogleSearch
import logging
import os
from modules import constants
import re
import yaml

from modules.ContextHandlers import ContextHandlers
import modules.Chat as chat
import modules.ChatSpeechProcessor as csp

class GoogleScraper():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A class for scraping Google search results based on a given search query."
	module_hook = "Chat_request_inner"


	def __init__(self):
		with open("configs.yaml", "r") as f:
			configs = yaml.safe_load(f)
		self.api_key = configs["keys"]["serp_api"]
		
		self.ch = ContextHandlers(constants.messages)
		self.chat = chat.instance
		self.start_prompt = """You are an internet connected chatbot and you have access to real-time information and updates from Google. If I ask you any question that may require internet access, always ask me if I would like you to search the web. If I say yes, respond with a search term as the FULL body of your response using a "tool form" in the following format: [search: news headlines]. You will NEVER immediately search the web as each time that trigger is activated it costs me money--always ask me first.
	Example #1:
	User: What is the weather today in st louis?
	Daisy: I don't have the answer with me right now. Would you like me to search the web?
	User: Yes, please.
	Daisy: [search: weather st louis]

	Example #2:
	User: How many airplanes are in the sky right now?
	Daisy: Im not quite sure of that answer without doing a web search. Would you like me to search the web?
	User: Yes.
	Daisy: [search: airplanes in the sky right now]"""

		logging.info("GoogleScraper: Adding start prompt")
		self.ch.add_message_object('system', self.start_prompt)


	def main(self, text, stop_event, stop_sound):
		"""Main method that takes in response_text and performs the web search, returning the search results."""
		#Find a search term in the response text (If --internet)
		web_response_text = ""
		logging.debug("GoogleScraper: Checking for tool forms")
		if "[search:" in text.lower():
			match = re.search(r"\[search:.*\]", text)
			if match:
				web_response = match.group()
				start = web_response.index(":") + 1
				end = web_response.index("]")
				search_query = web_response[start:end]

				logging.info(f"GoogleScraper: Searching the web for {search_query}...")

				params = {
				  "engine": "google",
				  "q": search_query,
				  "api_key": self.api_key
				}
				search = GoogleSearch(params)

				results = search.get_dict()
				organic_results = results["organic_results"]
				if len(organic_results):
					new_prompt="This is an automatic response to your tool form. Please respond to the user's last message using the information below.\n\n"
					for organic_result in organic_results:
						if("snippet" in organic_result):
							new_prompt += organic_result["snippet"]+"\n"

					self.ch.add_message_object('user', new_prompt)

					response_text = self.chat.request(self.ch.get_context_without_timestamp(), stop_event, stop_sound, True)
					return response_text
				
				else:
					return False
			else:
				return False
		else:
			return False