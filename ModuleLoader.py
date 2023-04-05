import os
import importlib.util
import json
import inspect
import logging
import json
import yaml

from modules import constants
from modules.ContextHandlers import ContextHandlers
ch = ContextHandlers(constants.messages)

class ModuleLoader:
	initialized = False
	
	def __init__(self, directory="modules"):
		if not ModuleLoader.initialized:
			logging.info("Loading modules...")
			self.directory = directory
			self.start_prompts = []
			self.hook_instances = {}
			self.loaded = False

			# Load modules
			self.available_modules = []
			self.get_available_modules()

			ModuleLoader.initialized = True

	def get_hook_instances(self):
		return self.hook_instances
		
	def get_available_modules(self):
		# Load enabled modules from config file
		with open('configs.yaml', 'r') as f:
			config = yaml.safe_load(f)

		enabled_modules = config['enabled_modules']
		# If the module has not been loaded yet, set the 'loaded' flag to True and create a JSON of available modules.
		if not self.loaded:
			self.loaded = True
			logging.info("Creating classes JSON")
			self.available_modules = []

			# Walk through the given directory and its subdirectories, and find Python files.
			for root, dirs, files in os.walk(self.directory):
				for filename in files:
					if filename.endswith('.py'):
						# Get the full path of the Python file and the relative path of the module.
						module_path = os.path.join(root, filename)
						rel_path = os.path.relpath(module_path, self.directory)

						# Convert the relative path to a Python module name.
						module_name = "modules." + rel_path[:-3].replace(os.sep, ".")

						# Check if the module is enabled

						enabled = True if module_name in enabled_modules else False

						# Attempt to import the module, and handle exceptions.
						try:
							module = importlib.import_module(module_name, package=None)
						except ModuleNotFoundError as e:
							logging.warning(f"Failed to load {module_name} due to missing dependency: {str(e)}")
							continue  # Skip this module and proceed with the next one

						# Find all classes in the module, and extract their methods and initialization parameters.
						for name in dir(module):
							if name == module.__name__.split(".")[-1]:
								obj = getattr(module, name)
								if isinstance(obj, type):
									class_methods = []
									init_params = []
									module_hook = getattr(obj, "module_hook", "")

									if module_hook:
										class_description = getattr(obj, "description", "No description.")
										module_dict = {"class_name": module_name, "description": class_description}

										# Add module_hook and enabled attributes to module dictionary
										module_dict["module_hook"] = module_hook
										module_dict["enabled"] = str(enabled)

										self.available_modules.append(module_dict)

										# If the class has a module_hook attribute, create an instance of it and add it to
										# the list of hook instances.
										if enabled and module_hook:
											if module_hook not in self.hook_instances:
													self.hook_instances[module_hook] = []
											if isinstance(obj, type) and obj.__module__ == module.__name__:
												instance = obj()
												self.hook_instances[module_hook].append(instance)
												logging.info(f"MODULE LOADED: {module_name} to {module_hook}")
											else:
												logging.debug(module_name + " failed to load.")
										elif not enabled:
											logging.debug("MODULE DISABLED: " + module_name)
										else:
											logging.debug("Class " + module_name + " has no module_hook value. Skipped.")
		
		return self.available_modules

		
	def enable_module(self, module_name):
		logging.info("Enabling module: " + module_name)
		with open('configs.yaml', 'r') as f:
			config = yaml.safe_load(f)

		if module_name not in config['enabled_modules']:
			config['enabled_modules'].append(module_name)
			with open('configs.yaml', 'w') as f:
				yaml.safe_dump(config, f)

			self.loaded = False
			return self.get_available_modules()
		else:
			logging.warning(module_name + " is already enabled.")

	def disable_module(self, module_name):
		logging.info("Disabling module: " + module_name)
		with open('configs.yaml', 'r') as f:
			config = yaml.safe_load(f)

		if module_name in config['enabled_modules']:
			config['enabled_modules'].remove(module_name)
			with open('configs.yaml', 'w') as f:
				yaml.safe_dump(config, f)

			self.loaded = False
			self.available_modules_json = self.get_available_modules()
		else:
			logging.warning(module_name + " is not enabled.")



instance = ModuleLoader("modules")