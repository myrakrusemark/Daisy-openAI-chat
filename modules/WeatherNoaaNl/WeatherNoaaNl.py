import requests
import logging
import threading
import yaml
import geocoder
from system_modules.Text import print_text


class WeatherNoaaNl:
	"""
	Description: A module that checks NOAA for the weather based on lat/lon
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module that checks NOAA for the weather based on lat/lon"
	module_hook = "Chat_request_inner"
	tool_form_name = "Weather"
	tool_form_description = "A module that provides current weather data based on location, or configured location. If no location is provided, respond with 'No Location' as the argument."
	tool_form_argument = "Location (City, Zip, Lat/Lon, etc.) / Or 'None' if not specified."

	def __init__(self, ml):
		self.ch = ml.ch
		self.stop_event = threading.Event()
		self.location = None
		self.latlon = None
		self.no_config_location = False

		#Set location information from configs.yaml
		with open("configs.yaml", "r") as f:
			self.configs = yaml.safe_load(f)
		if "location" in self.configs:
			self.location = self.configs["location"]
		if "latlon" in self.configs:
			self.latlon = self.configs["latlon"]

		self.grid_url = None

	def main(self, arg, stop_event):
		forecast = ""

		logging.info("WeatherNoaaNl: Getting weather...")

		arg = arg.strip().lower()
		# Get the location name from arg if it was passed
		if arg:
			if arg != "no location" and arg != "none":
				# A city name or other location was passed as an argument to main()
				self.location = arg

		#If we have a location but no coordinates, get the coordinates
		if self.location and not self.latlon:
			logging.info("Getting coordinates for: " + self.location)
			try:
				g = geocoder.arcgis(self.location)
				self.latlon = str(g.json['lat'])+","+str(g.json['lng'])
			except Exception as e:
				logging.error("Error getting coordinates: "+str(e))
		elif not self.latlon:
			#If we have neither a location nor coordinates, ask for the city
			self.no_config_location = True
			return "No location specified. It is critical that you ask the user for a location."

		# Get the weather forecast
		if self.latlon:
			forecast = self.get_forecast()

			# Get the detailed forecast for today
			if forecast:
				try:
					result = "Weather forecast for the location: " + forecast["properties"]["periods"][0]["detailedForecast"]+"\n"
					result += "\nCurrent conditions:\n"
					result += "Temperature: " + str(forecast["properties"]["periods"][0]["temperature"]) + " " + forecast["properties"]["periods"][0]["temperatureUnit"] + "\n"
					result += "Wind: " + forecast["properties"]["periods"][0]["windSpeed"] + " " + forecast["properties"]["periods"][0]["windDirection"] + "\n"
					result += "Humidity: " + str(forecast["properties"]["periods"][0]["relativeHumidity"]['value']) + "%\n"
					result += "Dew Point: " + str(forecast["properties"]["periods"][0]["dewpoint"]['value']) + " C\n"
					result += "Wind Direction: " + str(forecast["properties"]["periods"][0]["windDirection"]) + "\n"
					result += "Weather: " + forecast["properties"]["periods"][0]["shortForecast"] + "\n"
					result += "\nTonight:\n"
					result += "Temperature: " + str(forecast["properties"]["periods"][1]["temperature"]) + " " + forecast["properties"]["periods"][1]["temperatureUnit"] + "\n"
					result += "Weather: " + forecast["properties"]["periods"][1]["shortForecast"] + "\n"
					result += "\nThis week:\n"
					for day in forecast["properties"]["periods"][2:7]:
						result += day["name"] + ": "+day["detailedForecast"] + "\n"

				except:
					logging.error("Error getting forecast")
					return "Weather forecast: There was a server issue."
				logging.info("Result: "+result)

				if self.no_config_location:
					result += "\n\nIn your next response, give the weather forecast and then ask the user if they would like to set their location to "+self.location+".\n\n"

				# Return the weather forecast
				return result
			
			else:
				return "Weather forecast: There was an error and the forecast could not be retrieved for the location. " + str(forecast)
		return "Weather forecast: There was an error retrieving the right location. Please wait five minuts and try again."

	def get_forecast(self):
		"""Get the forecast from the grid url"""

		# Get the grid url
		if not self.grid_url:
			self._get_grid_url()

		# Get the forecast from the grid
		if self.grid_url:
			forecast_url = "{}/forecast".format(self.grid_url)
			print_text("Forecast URL: " + forecast_url, 'blue', "\n")
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
		url = f"https://api.weather.gov/points/{self.latlon}"
		logging.info("Grid URL: " + url)
		response = requests.get(url)

		if response.status_code == 200:
			data = response.json()

			# Get the URL for the grid data from the latlon JSON
			self.grid_url = data["properties"]["forecastGridData"]
		else:
			logging.error("Error connecting to the grid url API: "+str(response.status_code) + " " + f"https://api.weather.gov/points/{self.latlon}")
			self.grid_url = None

