import requests
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
	tool_form_name = "Weather"
	tool_form_description = "A module that provides current weather data based on location, or configured location. If no location is provided, respond with 'No Location' as the argument."
	tool_form_argument = "Location (City, Zip, Lat/Lon, etc.) / Or None if not specified."

	def __init__(self, ml):
		# initialize the ChatterBot instance
		self.ch = ml.ch
		# stop event for the thread
		self.stop_event = threading.Event()
		# load the configs.yaml file
		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		# get the latitude and longitude from configs.yaml
		self.latlon = self.configs["location"]
		# initialize the grid url
		self.grid_url = None
		# initialize the return prompt


	def main(self, arg, stop_event):
		logging.info("WeatherNoaaNl: Getting weather...")
		# Get the weather forecast
		forecast = self.get_forecast()
		# Get the detailed forecast for today
		try:
			result = "Weather forecast: "+forecast["properties"]["periods"][0]["detailedForecast"]
		except:
			logging.error("Error getting forecast")
			result = self.return_prompt_start+"Weather forecast: There was an error and the forecast could not be retrieved."
		# Print the weather forecast
		logging.info("WeatherNoaaNl: "+result)
		# Return the weather forecast
		return result


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


