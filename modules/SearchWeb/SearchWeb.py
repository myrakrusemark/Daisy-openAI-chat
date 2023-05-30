import logging
import json
from googleapiclient.discovery import build
import os

class SearchWeb:
    description = "A module for retrieving search results from Google Cloud."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

        self.credentials = self.load_credentials()

    def load_credentials(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, 'credentials.json')
        try:
            with open(filepath) as f:
                credentials = json.load(f)
            return credentials
        except FileNotFoundError:
            logging.error("GoogleCloudSearch: credentials.json file not found.")
            return None

    def main(self, arg, stop_event):
        logging.info("GoogleCloudSearch: Searching: " + arg)
        results = self.retrieve_search_results(arg)
        return results

    def retrieve_search_results(self, search_term):
        if not self.credentials:
            return "Error: Unable to load credentials."

        try:
            api_key = self.credentials.get('api_key')
            cse_id = self.credentials.get('cse_id')

            service = build("customsearch", "v1", developerKey=api_key)
            response = service.cse().list(q=search_term, cx=cse_id).execute()
            items = response.get('items', [])
            search_results = ""

            for item in items:
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                search_results += f"{title} ({link})\n{snippet}\n\n"

            return search_results
        except Exception as e:
            logging.error("GoogleCloudSearch: Error retrieving search results: " + str(e))
            return "Error: Unable to retrieve search results."
