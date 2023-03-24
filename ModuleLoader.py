import os
import importlib.util
import json
import inspect
import logging
import json

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
			self.available_modules_json = self.get_available_modules_json()

			ModuleLoader.initialized = True

	def get_hook_instances(self):
		return self.hook_instances
		
	def get_available_modules_json(self):
		# If the module has not been loaded yet, set the 'loaded' flag to True and create a JSON of available modules.
		if not self.loaded:
			self.loaded = True
			logging.info("Creating classes JSON")
			available_modules = []

			# Walk through the given directory and its subdirectories, and find Python files.
			for root, dirs, files in os.walk(self.directory):
				for filename in files:
					if filename.endswith('.py'):
						# Get the full path of the Python file and the relative path of the module.
						module_path = os.path.join(root, filename)
						rel_path = os.path.relpath(module_path, self.directory)

						# Convert the relative path to a Python module name.
						module_name = "modules." + rel_path[:-3].replace(os.sep, ".")

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

									# If the class has a module_hook attribute, add its methods and initialization parameters
									# to the available modules JSON.
									if module_hook:
										for method_name in dir(obj):
											method = getattr(obj, method_name)
											if callable(method) and not method_name.startswith("__"):
												method_description = method.__doc__ or "No description."
												try:
													sig = inspect.signature(method)
												except ValueError:
													logging.info("Invalid method, " + method_name)
													break
												method_args = [param.name for param in sig.parameters.values() if
															param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
												class_methods.append({"method_name": method_name, "description": method_description, "args": method_args})

										if hasattr(obj, '__init__'):
											init_sig = inspect.signature(obj.__init__)
											init_params = [param.name for param in init_sig.parameters.values() if
														param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and
														param.name != 'self']

										class_description = getattr(obj, "description", "No description.")
										available_modules.append({"class_name": obj.__name__, "description": class_description, "init_params": init_params, "methods": class_methods})

										# If the class has a module_hook attribute, create an instance of it and add it to
										# the list of hook instances.
										if module_hook:
											if module_hook not in self.hook_instances:
												self.hook_instances[module_hook] = []
											if isinstance(obj, type) and obj.__module__ == module.__name__:
												instance = obj()
												self.hook_instances[module_hook].append(instance)
												logging.info(f"MODULE LOADED: {module_name} to {module_hook}")
											else:
												logging.debug(module_name + " failed to load.")
										else:
											logging.debug("Class " + module_name + " has no module_hook value. Skipped.")

        	# Convert the list of available modules to a JSON string and return it.
			return_val = json.dumps(available_modules)
			return return_val


instance = ModuleLoader("modules")