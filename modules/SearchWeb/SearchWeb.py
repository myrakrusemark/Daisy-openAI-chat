from serpapi import GoogleSearch
import yaml

class SearchWeb:
    description = "A class for scraping Google search results based on a given search query."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ch = ml.ch
        with open("configs.yaml", "r") as f:
            self.configs = yaml.safe_load(f)
        self.api_key = self.configs["keys"]["serp_api"]
        self.grid_url = None

    def main(self, arg, stop_event):
        params = self.create_search_params(arg)
        search = self.create_google_search(params)
        results = self.get_search_results(search)
        if results:
            return self.format_search_results(results)
        else:
            return False

    def create_search_params(self, search_term):
        params = {
            "engine": "google",
            "q": search_term,
            "api_key": self.api_key
        }
        return params

    def create_google_search(self, params):
        try:
            search = GoogleSearch(params)
            return search
        except Exception as e:
            return False

    def get_search_results(self, search):
        if search:
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            return organic_results
        else:
            return None

    def format_search_results(self, results):
        search_results = ""
        for result in results:
            if "snippet" in result:
                search_results += '"'+result["title"] + '"\n'
                search_results += "["+result["link"] + "]\n"
                search_results += result["snippet"] + "\n\n"
        return search_results
