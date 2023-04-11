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
		self.start_prompt = """You are a Google searchbot. If I ask you any question that may require internet access, ask me if I would like you to search the web.

		If (only if) I am okay with that, respond with a "tool form" as the full body of your response, like so:

		[search: news headlines]"""

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
					new_prompt=f'''Respond to the user's message using the information below.
					Information: '''

					for organic_result in organic_results:
						if("snippet" in organic_result):
							new_prompt += organic_result["snippet"]+"\n"

					self.ch.add_message_object('system', new_prompt)

					response_text = self.chat.request(self.ch.get_context_without_timestamp(), stop_event, stop_sound, True)
					print("returned from googlescraper")
					return response_text
				
				else:
					return False
			else:
				return False
		else:
			return False