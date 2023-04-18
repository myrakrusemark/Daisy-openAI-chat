import os
import importlib.util
import inspect
import logging
import yaml
import time
import threading

from system_modules.ContextHandlers import ContextHandlers
ch = ContextHandlers()

class ModuleLoader:
	initialized = False
	
	def __init__(self, directory="modules"):
		if not ModuleLoader.initialized:
			self.directory = directory
			self.start_prompts = []
			self.hook_instances = {}
			self.loaded = False

			self.stop_event = threading.Event()
			self.thread = threading.Thread(target=self.update_modules_loop)

			# Load modules
			self.available_modules = []
			#self.get_available_modules()

			ModuleLoader.initialized = True
			

	def close(self):
		self.stop_event.set()
		self.thread.join()

	def start(self):
		self.thread.start()
		
	def get_hook_instances(self):
		return self.hook_instances
	
	def get_available_modules(self):
		if not self.loaded:
			self.loaded = True
			logging.info("Loading modules...")

			# Load enabled modules from config file
			with open('configs.yaml', 'r') as f:
				config = yaml.safe_load(f)

			enabled_modules = config['enabled_modules']
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
									module_dict = {"class_name": module_name, "description": class_description}

									# Add module_hook and enabled attributes to module dictionary
									module_dict["module_hook"] = module_hook
									module_dict["enabled"] = enabled

									self.available_modules.append(module_dict)

									# If the class has a module_hook attribute, create an instance of it and add it to
									# the list of hook instances.
									if enabled and module_hook:
										if isinstance(obj, type) and obj.__module__ == module.__name__:
											logging.info(f"MODULE LOADED: {module_name} to {module_hook}")
										else:
											logging.debug(module_name + " failed to load.")
									elif not enabled:
										logging.debug("MODULE DISABLED: " + module_name)
									else:
										logging.debug("Class " + module_name + " has no module_hook value. Skipped.")

			#Remove the module from available_modules if it's no loger in configs.yaml
			for available_module in self.available_modules:
				module_found = False
				if available_module["class_name"] not in enabled_modules:
					available_module["enabled"] = False
					logging.info(available_module["class_name"]+" has been disabled.")
			
			self.build_hook_instances()

		return self.available_modules
		
	def build_hook_instances(self):
		# Create a new dictionary to keep track of updated hook instances
		updated_hook_instances = {}

		# Iterate over the modules in the order they appear in configs.yaml
		with open('configs.yaml', 'r') as f:
			config = yaml.safe_load(f)
			for module_name in config['enabled_modules']:
				for module in self.available_modules:
					if module['class_name'] == module_name:
						if module['module_hook'] not in updated_hook_instances:
							updated_hook_instances[module['module_hook']] = []

						# Check if the instance already exists in hook_instances and use it if found
						existing_instance = None
						if module['module_hook'] in self.hook_instances:
							for instance in self.hook_instances[module['module_hook']]:
								if isinstance(instance, type) and instance.__class__.__name__ == module_name:
									existing_instance = instance
									break

						if existing_instance:
							instance = existing_instance
						else:
							module_class = importlib.import_module(module_name)
							for name in dir(module_class):
								if name == module_class.__name__.split(".")[-1]:
									obj = getattr(module_class, name)
									if isinstance(obj, type) and getattr(obj, "module_hook", "") == module['module_hook']:
										instance = obj()
										break

						# Add the updated instance to the updated_hook_instances
						updated_hook_instances[module['module_hook']].append(instance)

		# Notify and close removed instances
		for hook in self.hook_instances:
			for instance in self.hook_instances[hook]:
				if hook not in updated_hook_instances or instance not in updated_hook_instances[hook]:
					logging.info("Removing instance of " + instance.__class__.__name__ + " from " + hook + ".")
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
			config = yaml.safe_load(f)

		if module_name not in config['enabled_modules']:
			config['enabled_modules'].append(module_name)
			with open('configs.yaml', 'w') as f:
				yaml.safe_dump(config, f)

			self.loaded = False
		else:
			logging.warning(module_name + " is already enabled.")
		time.sleep(0.5)
		return self.get_available_modules()

	def disable_module(self, module_name):
		logging.info("Disabling module: " + module_name)
		with open('configs.yaml', 'r') as f:
			config = yaml.safe_load(f)

		if module_name in config['enabled_modules']:
			config['enabled_modules'].remove(module_name)
			with open('configs.yaml', 'w') as f:
				yaml.safe_dump(config, f)

			self.loaded = False
		else:
			logging.warning(module_name + " is already disabled.")
		time.sleep(0.5)
		return self.get_available_modules()



instance = ModuleLoader("modules")
instance.start()