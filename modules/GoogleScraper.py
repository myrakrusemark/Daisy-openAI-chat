from serpapi import GoogleSearch
import yaml

class GoogleScraper():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A class for scraping Google search results based on a given search query."
	module_hook = "Chat_request_inner"
	tool_form_name = "Google"
	tool_form_description = "A module that scrapes Google search results."
	tool_form_argument = "Search term"

	def __init__(self, ml):
		self.ch = ml.ch

		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		
		self.api_key = self.configs["keys"]["serp_api"]

		self.grid_url = None

	
	def main(self, arg, stop_event):


		# Create the parameters for the Google Search API.
		params = {
			"engine": "google",
			"q": arg,
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
		search_results = ""
		if len(organic_results):
			for organic_result in organic_results:
				if("snippet" in organic_result):
					search_results += organic_result['snippet']+"\n"

			return search_results
		else:
			return False
