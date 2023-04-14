import os
import requests
import time
from datetime import datetime
import system_modules.ContextHandlers as ch
import logging
import threading
import yaml
import re

class WeatherNoaaNl:
	"""
	Description: A module that checks NOAA for the weather based on lat/lon
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module that checks NOAA for the weather based on lat/lon"
	module_hook = "Chat_request_inner"

	def __init__(self):
		# initialize the ChatterBot instance
		self.ch = ch.instance
		# stop event for the thread
		self.stop_event = threading.Event()
		# load the configs.yaml file
		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		# get the latitude and longitude from configs.yaml
		self.latlon = self.configs["location"]
		# initialize the grid url
		self.grid_url = None
		# initialize the start prompt
		self.start_prompt = """You are a Weather Bot: If I ask you for the weather, respond with a "tool form": [WeatherNoaaNl: forecast]. Then formulate your response based on the system message."""
		# add the start prompt to the ChatterBot
		logging.info("WeatherNoaaNl: Adding start prompt")
		self.ch.add_message_object('system', self.start_prompt)
		# initialize the return prompt
		self.return_prompt_start = "Respond using the real-time weather forecast below.\n"



	def check(self, text):
		# Check for the presence of a tool form in the text.
		logging.debug("WeatherNoaaNl: Checking for tool forms "+text)
		found_tool_form = False
		if "[WeatherNoaaNl:" in text:
			self.match = re.search(r"\[WeatherNoaaNl:\s*(.*?)\]", text)
			if self.match:
				# Found a tool form.
				logging.info("WeatherNoaaNl: Found tool form")
				found_tool_form = True
		return found_tool_form

	def main(self, text, stop_event):
		logging.info("WeatherNoaaNl: Getting weather...")
		# Get the weather forecast
		forecast = self.get_forecast()
		# Get the detailed forecast for today
		try:
			prompt = self.return_prompt_start+forecast["properties"]["periods"][0]["detailedForecast"]
		except:
			prompt = self.return_prompt_start+"I'm sorry, I can't get the weather forecast."
		# Print the weather forecast
		logging.info("WeatherNoaaNl: "+prompt)
		# Return the weather forecast
		return prompt


	def get_forecast(self):
		"""Get the forecast from the grid url"""

		# Get the grid url
		if not self.grid_url:
			self._get_grid_url()

		# Get the forecast from the grid
		forecast_url = "{}/forecast".format(self.grid_url)
		response = requests.get(forecast_url)
		if response.status_code == 200:
			return response.json()
		else:
			return None

	def _get_grid_url(self):
		"""Get the URL for the grid data for the current latlon."""
		# Get the JSON data for the latlon
		response = requests.get(f"https://api.weather.gov/points/{self.latlon}")

		if response.status_code == 200:
			data = response.json()

			# Get the URL for the grid data from the latlon JSON
			self.grid_url = data["properties"]["forecastGridData"]
			print(self.grid_url)
		else:
			logging.error("Error connecting to the API")



	def close(self):
		"""Stop the thread and wait for it to end."""
		self.stop_event.set()


