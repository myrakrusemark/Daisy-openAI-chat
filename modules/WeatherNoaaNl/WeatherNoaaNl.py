import os
import requests
import time
from datetime import datetime
import modules.ContextHandlers as ch
import logging
import threading

class WeatherNoaaNl:
    """
    Description: A module that checks NOAA for the weather based on lat/lon
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that checks NOAA for the weather based on lat/lon"
    module_hook = "Main_start"

    def __init__(self):
        self.stop_event = threading.Event()
        self.latlon = os.environ.get('LATLON', '38.627,-90.1994')
        self.grid_url = None

        self.forecast_prompt = f'''
         Current weather forecast and conditions for the current location are below. 
         If I ask for the weather or about any current weather conditions, that information is below. Give your answer in a natural way:
         ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) [WeatherNoaaNl]
        '''

        self.ch = ch.instance

    def get_forecast(self):
        if not self.grid_url:
            self._get_grid_url()
        response = requests.get(f"{self.grid_url}/forecast")
        return response.json()

    def _get_grid_url(self):
        response = requests.get(f"https://api.weather.gov/points/{self.latlon}")
        data = response.json()
        self.grid_url = data["properties"]["forecastGridData"]
        print(self.grid_url)

    def close(self):
        self.stop_event.set()

    def main(self):
        while not self.stop_event.is_set():
            forecast = self.get_forecast()
            self.forecast_prompt += forecast["properties"]["periods"][0]["detailedForecast"]
            print(self.forecast_prompt)
            message = self.ch.get_last_message_object("user")
            if message and "[WeatherNoaaNl]" in message["content"]:
                print("TAG IN MESSAGE")
                self.ch.replace_last_message_object("user", self.forecast_prompt)
            else:
                logging.info("Adding 'WeatherNoaaNl' start prompt to context")
                self.ch.add_message_object('user', self.forecast_prompt)
            time.sleep(600) # pause for 10 minutes between forecast retrievals
