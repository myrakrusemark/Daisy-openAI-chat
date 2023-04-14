from dotenv import load_dotenv
import openai
from serpapi import GoogleSearch
import logging
import os
import re
import yaml

import system_modules.ContextHandlers as ch
import system_modules.Chat as chat
import system_modules.ChatSpeechProcessor as csp

class GoogleScraper():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A class for scraping Google search results based on a given search query."
	module_hook = "Chat_request_inner"

	def __init__(self):
		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		
		self.api_key = self.configs["keys"]["serp_api"]

		self.ch = ch.instance

		self.grid_url = None

		self.start_prompt = """You are a Google Scraper Bot: If I ask you any question that may require internet access, ask me if I would like to search the web. Then respond with a "tool form" containing the search term: [GoogleScraper: search term]. Then formulate your response based on the system message."""

		self.ch.add_message_object('system', self.start_prompt)

		
	def check(self, text):
		logging.debug("GoogleScraper: Checking for tool forms")
		found_tool_form = False
		if "[GoogleScraper:" in text:
			self.match = re.search(r"\[GoogleScraper:\s*(.*?)\]", text)
			if self.match:
				logging.info("GoogleScraper: Found tool form")
				found_tool_form = True
		return found_tool_form
	
	def main(self, text, stop_event):
		# Get the search query from the processed string.
		try:
			processed_string = self.match.group()
		except Exception as e:
			return False

		try:
			start = processed_string.index(":") + 1
			end = processed_string.index("]")
			search_query = processed_string[start:end]
		except Exception as e:
			return False

		# Create the parameters for the Google Search API.
		params = {
			"engine": "google",
			"q": search_query,
			"api_key": self.api_key
		}

		# Create a new instance of the GoogleSearch class.
		try:
			search = GoogleSearch(params)
		except Exception as e:
			return False

		# Get a dictionary of the search results.
		results = search.get_dict()
		organic_results = results["organic_results"]
		# If there are search results, create a new prompt with the snippets.
		if len(organic_results):
			prompt=f'''Respond using the search results below.\n'''

			for organic_result in organic_results:
				if("snippet" in organic_result):
					prompt += organic_result["snippet"]+"\n"

			return prompt
		else:
			return False
