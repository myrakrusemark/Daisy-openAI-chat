import requests
import logging
import threading
import yaml
from geopy.geocoders import Nominatim

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
		self.ch = ml.ch
		self.stop_event = threading.Event()
		self.geolocator = Nominatim(user_agent="MyApp")
		self.latlon = None

		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
			self.location = self.configs["location"]
		self.grid_url = None

	def main(self, arg, stop_event):
		logging.info("WeatherNoaaNl: Getting weather...")

		arg = arg.strip().lower()
		# Get the latlon from the location name
		if arg:
			print("arg: '" + arg+"'")
			if arg != "no location" and arg != "none":
				# A city name or other location was passed as an argument to main()
				self.location = arg
		else:
			logging.info("WeatherNoaaNl: No location passed as argument. Using configured location.")

		logging.info("WeatherNoaaNl: Getting coordinates for: " + self.location)
		self.latlon = self.geolocator.geocode(self.location)

		# Get the weather forecast
		if self.latlon:
			forecast = self.get_forecast()
			# Get the detailed forecast for today
			if forecast:
				try:
					result = "Weather forecast: " + forecast["properties"]["periods"][0]["detailedForecast"]
				except:
					logging.error("Error getting forecast")
					result = "Weather forecast: There was an error and the forecast could not be retrieved for "+self.location+". If the city is outside the US, data may not be available." + str(forecast)
				# Print the weather forecast
				logging.info("WeatherNoaaNl: " + result)
				# Return the weather forecast
				return result
			else:
				return "Weather forecast: There was an error and the forecast could not be retrieved for "+self.location+". " + str(forecast)
		return "Weather forecast: There was an error retrieving the right location based on the location name."

	def get_forecast(self):
		"""Get the forecast from the grid url"""

		# Get the grid url
		if not self.grid_url:
			self._get_grid_url()

		# Get the forecast from the grid
		if self.grid_url:
			forecast_url = "{}/forecast".format(self.grid_url)
			logging.info("Forecast URL: " + forecast_url)
			response = requests.get(forecast_url)
			if response.json():
				return response.json()
			else:
				return "There was an error. Status code: " + response.status_code
		else:
			return None
			 

	def _get_grid_url(self):
		"""Get the URL for the grid data for the current latlon."""
		# Get the JSON data for the latlon
		url = f"https://api.weather.gov/points/{self.latlon.latitude},{self.latlon.longitude}"
		logging.info("Grid URL: " + url)
		response = requests.get(url)

		if response.status_code == 200:
			data = response.json()

			# Get the URL for the grid data from the latlon JSON
			self.grid_url = data["properties"]["forecastGridData"]
			print(self.grid_url)
		else:
			logging.error("Error connecting to the grid url API: "+str(response.status_code) + " " + f"https://api.weather.gov/points/{self.latlon}")
			self.grid_url = None

