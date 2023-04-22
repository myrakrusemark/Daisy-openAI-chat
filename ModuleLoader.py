import os
import importlib.util
import inspect
import logging
import yaml
import time
import threading
from ruamel.yaml import YAML
yaml = YAML()
from system_modules.Text import print_text



class ModuleLoader:
	initialized = False
	
	def __init__(self, ch, directory="modules"):
		self.ch = ch
		if not ModuleLoader.initialized:
			ModuleLoader.initialized = True

			self.directory = directory
			self.start_prompts = []
			self.hook_instances = {}
			self.loaded = False

			self.stop_event = threading.Event()
			self.thread = threading.Thread(target=self.update_modules_loop)

			# Load modules
			self.available_modules = []


			# Load enabled modules from config file
			with open('configs.yaml', 'r') as f:
				self.configs = yaml.load(f)
			

	def close(self):
		self.stop_event.set()
		self.thread.join()

	def start(self):
		self.thread.start()
		
	def get_hook_instances(self):
		return self.hook_instances
		
	def get_available_modules(self):
		# Load enabled modules from config file
		with open('configs.yaml', 'r') as f:
			self.configs = yaml.load(f)

		enabled_modules = self.configs['enabled_modules']
		if not self.loaded:
			self.loaded = True
			logging.info("Updating modules...")

			for module_name in enabled_modules:
				# If module is in configs.yaml, it is enabled.
				enabled = True
				# Check if the module is already in available modules
				module_in_available = False
				for module in self.available_modules:
					if module['class_name'] == module_name:
						module_in_available = True
						if module_in_available:
							module["enabled"] = enabled
						break
				# Add the module if it's NOT in available modules
				if not module_in_available:
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
								module_hook = getattr(obj, "module_hook", "")

								if module_hook:
									class_description = getattr(obj, "description", "No description.")
									tool_form_name = getattr(obj, "tool_form_name", None)
									tool_form_description = getattr(obj, "tool_form_description", None)
									tool_form_argument = getattr(obj, "tool_form_argument", None)

									# Add module_hook and enabled attributes to module dictionary
									module_dict = {}
									module_dict["class_name"] = module_name
									module_dict["description"] = class_description
									module_dict["module_hook"] = module_hook
									module_dict["enabled"] = enabled
									if tool_form_name:
										module_dict["tool_form_name"] = tool_form_name
									if tool_form_description:
										module_dict["tool_form_description"] = tool_form_description
									if tool_form_argument:
										module_dict["tool_form_argument"] = tool_form_argument

									self.available_modules.append(module_dict)

									# If the class has a module_hook attribute, create an instance of it and add it to
									# the list of hook instances.
									if enabled and module_hook:

										#Module loaded
										pass

									elif not enabled:
										logging.debug("MODULE DISABLED: " + module_name)
									else:
										logging.debug("Class " + module_name + " has no module_hook value. Skipped.")

			#If config.yaml item is no longer available, set enabled to False
			for available_module in self.available_modules:
				if available_module["class_name"] not in enabled_modules:
					available_module["enabled"] = False

			self.build_hook_instances()
		return self.available_modules

		
	def build_hook_instances(self):
		# Create a new dictionary to keep track of updated hook instances
		updated_hook_instances = {}

		# Iterate over the modules in the order they appear in configs.yaml
		for module_name in self.configs['enabled_modules']:
			for module in self.available_modules:
				
				if module['class_name'] == module_name:
					if module['module_hook'] not in updated_hook_instances:
						updated_hook_instances[module['module_hook']] = []

					# Check if the instance already exists in hook_instances and use it if found
					existing_instance = None

					#Get the module object
					module_class = importlib.import_module(module_name)
					obj = getattr(module_class, module_name.split(".")[-1])

					#Check if the module already exists
					if module['module_hook'] in self.hook_instances:
						for instance in self.hook_instances[module['module_hook']]:
							if isinstance(obj, type) and instance.__class__.__name__ == module_name.split(".")[-1]:
								existing_instance = instance
								break

					#If so, use it instead
					if existing_instance:
						instance = existing_instance
					else:
						for name in dir(module_class):
							if name == module_class.__name__.split(".")[-1]:
								if isinstance(obj, type):
									instance = obj(self)
									instance.ch = self.ch  # Add self.ch to the instance
									instance.ml = self  # Add self to the instance
								if hasattr(instance, "start") and callable(getattr(instance, "start")):
									instance.start()

					# Add the updated instance to the updated_hook_instances
					updated_hook_instances[module['module_hook']].append(instance)
					print_text("MODULE LOADED: ", "green", "", "italic")
					print_text(module_name+" to "+module['module_hook'], None, "\n")

					break

		# Notify and close removed instances
		for hook in self.hook_instances:
			for instance in self.hook_instances[hook]:
				if hook not in updated_hook_instances or instance not in updated_hook_instances[hook]:

					print_text("MODULE REMOVED: ", "green", "", "italic")
					print_text(instance.__class__.__name__ + " from " + hook + ".", None, "\n")

					if hasattr(instance, 'close') and callable(getattr(instance, 'close')):
						instance.close()

		#Replace existing object with the new one
		self.hook_instances = updated_hook_instances

	def update_modules_loop(self):
		last_modified_time = 0
		while True:
			current_modified_time = os.path.getmtime("configs.yaml")
			if current_modified_time > last_modified_time:
				self.loaded = False
				self.get_available_modules()
				
				last_modified_time = current_modified_time

			time.sleep(1)

	def enable_module(self, module_name):
		logging.info("Enabling module: " + module_name)
		with open('configs.yaml', 'r') as f:
			config = yaml.load(f)

		if module_name not in config['enabled_modules']:
			config['enabled_modules'].append(module_name)
			with open('configs.yaml', 'w') as f:
				yaml.dump(config, f)

			self.loaded = False
		else:
			logging.warning(module_name + " is already enabled.")
		time.sleep(0.5)
		return self.get_available_modules()

	def disable_module(self, module_name):
		logging.info("Disabling module: " + module_name)
		with open('configs.yaml', 'r') as f:
			config = yaml.load(f)

		if module_name in config['enabled_modules']:
			config['enabled_modules'].remove(module_name)
			with open('configs.yaml', 'w') as f:
				yaml.dump(config, f)

			self.loaded = False
		else:
			logging.warning(module_name + " is already disabled.")
		time.sleep(0.5)
		return self.get_available_modules()



