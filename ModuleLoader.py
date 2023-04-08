import os
import importlib.util
import inspect
import logging
import yaml
import time
import threading

start_prompt_Daisy = "You are Daisy, a voice assistant based on chatGPT, a large language model trained by OpenAI. You speak in confident but concise responses, about two sentences long. You are having a real-world vocal conversation. Current date: " + datetime.now().strftime("%Y-%m-%d")   
messages=[{"role": "user", "timestamp":"", "content": start_prompt_Daisy}]
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
			#self.get_available_modules()

			ModuleLoader.initialized = True

	def get_hook_instances(self):
		return self.hook_instances
	
	def get_available_modules(self):
		# Load enabled modules from config file
		with open('configs.yaml', 'r') as f:
			config = yaml.safe_load(f)

		enabled_modules = config['enabled_modules']
		# If the module has not been loaded yet, set the 'loaded' flag to True and create available modules.
		if not self.loaded:
			self.loaded = True
			logging.info("Creating classes for available modules...")
			#self.available_modules = []

			# Walk through the given directory and its subdirectories, and find Python files.
			for root, dirs, files in os.walk(self.directory):
				for filename in files:
					if filename.endswith('.py'):
						# Get the full path of the Python file and the relative path of the module.
						module_path = os.path.join(root, filename)
						rel_path = os.path.relpath(module_path, self.directory)

						# Convert the relative path to a Python module name.
						module_name = "modules." + rel_path[:-3].replace(os.sep, ".")

						# Check if the module is enabled in configs.yaml
						enabled = True if module_name in enabled_modules else False

						# Check if the module is already in available modules
						module_in_available = False
						for module in self.available_modules:
							if module['class_name'] == module_name:
								module_in_available = True
								if module_in_available:
									module["enabled"] = enabled
								break

						#Remove the module from available_modules if it's not enabled
						if not enabled and module_in_available:
							#self.available_modules = [module for module in self.available_modules if module['class_name'] != module_name]
							self.rebuild_hook_instances()

						# Add the module if it's NOT in available modules
						elif not module_in_available:
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
											module_dict["enabled"] = enabled

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
		
	def rebuild_hook_instances(self):
		# Create a new dictionary to keep track of updated hook instances
		updated_hook_instances = {}

		for module in self.available_modules:
			if module['enabled'] == True:
				module_hook = module['module_hook']
				module_name = module['class_name']
				try:
					module_class = importlib.import_module(module_name)
					for name in dir(module_class):
						if name == module_class.__name__.split(".")[-1]:
							obj = getattr(module_class, name)
							if isinstance(obj, type) and getattr(obj, "module_hook", "") == module_hook:
								# Check if the instance already exists in hook_instances and use it if found
								existing_instance = None
								if module_hook in self.hook_instances:
									for instance in self.hook_instances[module_hook]:
										if isinstance(instance, obj):
											existing_instance = instance
											break

								if existing_instance:
									instance = existing_instance
								else:
									instance = obj()

								# Add the updated instance to the updated_hook_instances
								if module_hook not in updated_hook_instances:
									updated_hook_instances[module_hook] = []
								updated_hook_instances[module_hook].append(instance)
				except Exception as e:
					logging.warning(f"Failed to update hook instance for {module_name}: {str(e)}")

		# Remove instances that are no longer needed
		for hook in self.hook_instances:
			for instance in self.hook_instances[hook]:
				if hook not in updated_hook_instances or instance not in updated_hook_instances[hook]:
					logging.info("Removing instance of " + instance.__class__.__name__ + " from " + hook + ".")
					if hasattr(instance, 'close') and callable(getattr(instance, 'close')):
						instance.close()


		# Add updated instances to self.hook_instances
		for hook in updated_hook_instances:
			if hook not in self.hook_instances:
				self.hook_instances[hook] = []
			for instance in updated_hook_instances[hook]:
				if instance not in self.hook_instances[hook]:
					logging.info("Adding instance of " + instance.__class__.__name__ + " to " + hook + ".")
					self.hook_instances[hook].append(instance)

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
thread = threading.Thread(target=instance.update_modules_loop)
thread.start()
