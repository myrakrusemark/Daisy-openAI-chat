from dotenv import load_dotenv
import openai
from serpapi import GoogleSearch
import logging
import os
import re

from modules.ContextHandlers import ContextHandlers
import modules.Chat as chat
import modules.ChatSpeechProcessor as csp
start_prompt_Daisy = "You are Daisy, a voice assistant based on chatGPT, a large language model trained by OpenAI. You speak in confident but concise responses, about two sentences long. You are having a real-world vocal conversation. Current date: " + datetime.now().strftime("%Y-%m-%d")
messages=[{"role": "user", "timestamp":"", "content": start_prompt_Daisy}]
class GoogleScraper():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A class for scraping Google search results based on a given search query."
	module_hook = "Chat_chat_inner"


	def __init__(self):
		self.api_key = os.environ["SERPAPI_KEY"]
		self.ch = ContextHandlers(messages)
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
		self.ch.add_message_object('user', self.start_prompt)


	def main(self, response_text):
		"""Main method that takes in response_text and performs the web search, returning the search results."""
		#Find a search term in the response text (If --internet)
		web_response_text = ""
		logging.info("GoogleScraper: Checking for tool forms")
		if "[search:" in response_text.lower():
			match = re.search(r"\[search:.*\]", response_text)
			if match:
				web_response = match.group()
				start = web_response.index(":") + 1
				end = web_response.index("]")
				search_query = web_response[start:end]
				print(f"Searching the web ({search_query})...")
				csp.instance.tts("Searching the web.")
				self.ch.add_message_object('assistant', 'Searching the web... [search:'+search_query+']')

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

					#Get the web answer
					web_response_text = self.chat.request(self.ch.get_context_without_timestamp())
				else:
					web_response_text = "Sorry, either there was an error or there are no results."

			return web_response_text
		else:
			return response_text
