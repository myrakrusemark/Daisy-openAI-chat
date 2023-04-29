import logging
import geocoder

from ruamel.yaml import YAML
yaml = YAML()
yaml.allow_duplicate_keys = True


class SetLocation:
	description = "A module that sets the current physical location."
	module_hook = "Chat_request_inner"
	tool_form_name = "Set Location"
	tool_form_description = """Sets the current physical location for the user. Accepts a location name, zip code, or address."""
	tool_form_argument = "Location (City, Zip, Lat/Lon, etc.) / Or 'None' if not specified."


	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch




	def main(self, arg, stop_event):
		location = arg
		latlon = None

		if not arg:
			return "No location provided. Ask the user what their location is."
		#Get the coordinates for the location
		try:
			g = geocoder.arcgis(location)
			latlon = str(g.json['lat'])+","+str(g.json['lng'])
		except Exception as e:
			logging.error("Error getting coordinates: "+str(e))

		#If no latlon, then the service is down, or the location is invalid
		if not latlon:
			prompt = "Error getting coordinates for "+arg+". Please try again in about 5 minutes."
			return prompt
		
		#Get the best location name from the coordinates
		try:
			g = geocoder.arcgis([g.json['lat'], g.json['lng']], method='reverse')
			location = g.json['address']
		except Exception as e:
			logging.error("Error getting location name: "+str(e))


		try:
			# Load enabled modules from config file
			configs = None
			with open('configs.yaml', 'r') as f:
				configs = yaml.load(f)
				#Set the location and coordinates in configs.yaml
				if "location" in configs:
					configs['location'] = ""
				if "latlon" in configs:
					configs['latlon'] = ""

				configs['location'] = location
				configs['latlon'] = latlon

				with open('configs.yaml', 'w') as f:
					print(configs)
					yaml.dump(configs, f)
		except Exception as e:
			logging.error("Error setting location in configs.yaml: "+str(e))
			prompt = "Error setting location in configs.yaml. Please try again in about 5 minutes."
			return prompt

		#Return the location and coordinates
		prompt = "Let the user know that the location and coordinates UPDATED SUCCESSFULLY for "+location
		return prompt
			
