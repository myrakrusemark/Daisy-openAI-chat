import logging
import geocoder
from ruamel.yaml import YAML

yaml = YAML()
yaml.allow_duplicate_keys = True


class SetLocation:
    description = "A module that sets the current physical location."
    module_hook = "Chat_request_inner"
    tool_form_name = "Set Location"
    tool_form_description = "Sets the current physical location for the user. Accepts a location name, zip code, or address."
    tool_form_argument = "Location (City, Zip, Lat/Lon, etc.) / Or 'None' if not specified."

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        location = arg
        latlon = None

        if not arg:
            return "No location provided. Ask the user what their location is."

        latlon = self.get_coordinates(location)
        if not latlon:
            return "Error getting coordinates for {}. Please try again in about 5 minutes.".format(arg)

        location = self.get_location_name(latlon)

        if not self.set_location_configs(location, latlon):
            return "Error setting location in configs.yaml. Please try again in about 5 minutes."

        return "Location and coordinates updated successfully for {}".format(location)

    def get_coordinates(self, location):
        try:
            g = geocoder.arcgis(location)
            latlon = "{},{}".format(g.json['lat'], g.json['lng'])
            return latlon
        except Exception as e:
            logging.error("Error getting coordinates: {}".format(str(e)))
            return None

    def get_location_name(self, latlon):
        try:
            g = geocoder.arcgis(latlon, method='reverse')
            location = g.json['address']
            return location
        except Exception as e:
            logging.error("Error getting location name: {}".format(str(e)))
            return None

    def set_location_configs(self, location, latlon):
        try:
            configs = None
            with open('configs.yaml', 'r') as f:
                configs = yaml.load(f)
                if "location" in configs:
                    configs['location'] = ""
                if "latlon" in configs:
                    configs['latlon'] = ""

                configs['location'] = location
                configs['latlon'] = latlon

            with open('configs.yaml', 'w') as f:
                yaml.dump(configs, f)
            return True
        except Exception as e:
            logging.error("Error setting location in configs.yaml: {}".format(str(e)))
            return False
