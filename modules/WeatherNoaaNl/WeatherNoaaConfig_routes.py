from flask import render_template, request, redirect, url_for

from dotenv import set_key
import os

class WeatherNoaaConfig_routes:
    """
    Description: A module that adds the WeatherNoaaConfig route to the app.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that adds the WeatherNoaaConfig routes to the app."
    module_hook = "WebConfig_add_routes"

    def weather_noaa_config(self):
        latlon = os.environ.get('LATLON', '0,0')
        return render_template('weather_noaa_config.html', latlon=latlon)

    weather_noaa_config.is_route = True
    weather_noaa_config.route_path = '/weather_noaa_config'

    def _set_weather_noaa_config(self):
        latlon = request.args.get('latlon')
        set_key('.env', 'LATLON', latlon)
        os.environ['LATLON'] = latlon
        return redirect(url_for('weather_noaa_config'))

    _set_weather_noaa_config.is_route = True
    _set_weather_noaa_config.route_path = '/set_weather_noaa_config'
