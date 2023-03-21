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
    def __init__(self, directory=""):
        logging.info("Loading modules...")
        self.directory = directory
        self.loaded_classes = []
        self.start_prompts = []




        #>>>>>>>>>>>>>>>Define and register module_hooks here<<<<<<<<<<<<<<<
        self.Chat_chat_inner_instances = []
        globals()["Chat_chat_inner_instances"] = self.Chat_chat_inner_instances

        self.Main_start_instances = []
        globals()["Main_start_instances"] = self.Main_start_instances

        self.Tts_instances = []
        globals()["Tts_instances"] = self.Tts_instances

        self.WebConfig_add_routes_instances = []
        globals()["WebConfig_add_routes_instances"] = self.WebConfig_add_routes_instances
        #>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<




        #Load modules and capabilities prompts and classes
        self.available_modules_json = self.get_available_modules_json()
        self.insert_start_prompts_to_context()

    def get_available_modules_json(self):
        logging.info("Creating classes JSON")
        available_modules = []
        for filename in os.listdir(self.directory):
            if filename.endswith('.py'):
                module_name = filename[:-3]  # remove .py extension
                try:
                    module = importlib.import_module(self.directory + "." + module_name, package=None)
                except ModuleNotFoundError as e:
                    logging.warning(f"Failed to load {module_name} due to missing dependency: {str(e)}")
                    continue  # Skip this module and proceed with the next one
                module = importlib.import_module(self.directory + "." + module_name, package=None)
                for name in dir(module):
                    if name == module_name:
                        obj = getattr(module, name)
                        if isinstance(obj, type):
                            class_methods = []
                            init_params = []
                            module_hook = getattr(obj, "module_hook", "")
                            if module_hook:  # Last bit to make it a valid hooked module
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
                                        class_methods.append(
                                            {"method_name": method_name, "description": method_description, "args": method_args})
                                if hasattr(obj, '__init__'):
                                    init_sig = inspect.signature(obj.__init__)
                                    init_params = [param.name for param in init_sig.parameters.values() if
                                                   param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and
                                                   param.name != 'self']
                                class_description = getattr(obj, "description", "No description.")
                                available_modules.append(
                                    {"class_name": obj.__name__, "description": class_description, "init_params": init_params,
                                     "methods": class_methods})
                                if module_hook + "_instances" in globals():
                                    target_instance_list = globals()[module_hook + "_instances"]
                                    # Check if the object is a class and has the same name as the module
                                    if isinstance(obj, type) and obj.__module__ == module.__name__:
                                        # Instantiate the class and append the instance to the array
                                        instance = obj()
                                        target_instance_list.append(instance)
                                        logging.info(f"MODULE LOADED: {module_name} to {module_hook}")
                                        # Check if instance has start_prompt and add it to self.start_prompts
                                        if hasattr(instance, "start_prompt"):
                                            self.start_prompts.append({"module_name":module_name, "start_prompt":instance.start_prompt})
                                    else:
                                        logging.debug(module_name + " failed to load.")
                                else:
                                    logging.debug(module_hook + " module_hook not available.")
                            else:
                                logging.debug("Class " + module_name + " has no module_hook value. Skipped.")
        return_val = json.dumps(available_modules)
        return return_val

    def insert_start_prompts_to_context(self):
        for start_prompt in self.start_prompts:
            logging.info("Inserting start prompt for "+start_prompt["module_name"])
            ch.add_message_object('user', start_prompt["start_prompt"])




    #def insert_capabilities_prompt_to_context(self):
    #    logging.info("Inserting Available Capabilities prompt.")
    #    ch.add_message_object('user', self.start_prompt)

instance = ModuleLoader("modules")