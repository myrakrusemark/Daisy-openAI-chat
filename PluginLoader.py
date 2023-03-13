import os
import importlib.util
import json
import inspect
import logging
import json

from plugins import constants
from plugins.ContextHandlers import ContextHandlers
ch = ContextHandlers(constants.messages)



class PluginLoader:
    def __init__(self, directory=""):
        logging.info("Loading modules...")
        self.directory = directory
        self.loaded_classes = []

        #Define and register module_hooks here
        self.Chat_chat_inner_instances = []
        globals()["Chat_chat_inner_instances"] = self.Chat_chat_inner_instances

        self.Main_start_instances = []
        globals()["Main_start_instances"] = self.Main_start_instances

        #Load modules and capabilities prompts and classes
        self.available_modules_json = self.get_available_modules_json()
        self.new_capabilities_prompt = f'''
You are Daisy, a chat assistant running on a dedicated device. You have one or more added capabilities available to you that you can use whenever you feel like you need to. Below is a JSON object with a list of classes that you can call. Each class comes with a description, and the methods it contains. This way you know exactly what you can do, so you can work with me to solve problems, look up information, and play games.
{self.available_modules_json}
When I ask you any question that might require one of your new skills, I would like you to respond in a way that my program can use to trigger the methods available to you. You will receive the output as a response. This is called a "tool former". A tool former is a consistent command that you provide that my code is always watching out for. Here are a few hypothetical examples of calls to classes and their methods. NOTE: These may not be included in the capabilities in the JSON--they are only examples.
Example #1:
    User: What is 5+6?
    Assistant: [calculator: 5+6] #You will never include any text in your tool former message.
    User: This is an automatic response to your tool form. Please respond to the user's last message using the information below.
        637.59
    Assistant: Five plus six equals eleven.
Example #2:
    User: What is the weather in St. Louis right now?
    Assistant: [search: weather st louis]
    User: This is an automatic response to your tool form. Please respond to the user's last message using the information below.
        56F, Winds SSW 5mph with gusts reaching 15mph. Partly cloudy all night, clearing by morning.
    Assistant: Tonight will be chilly, 56 degrees. Be sure to wear a coat because the 15mph winds could make it feel even colder.   
The above are only examples and it is okay that they may not be included in the JSON.   
        '''
        self.insert_capabilities_prompt_to_context()
        #self.import_and_instantiate_classes()


    def get_available_modules_json(self):
        logging.info("Creating classes JSON")
        available_modules = []
        for filename in os.listdir(self.directory):
            if filename.endswith('.py'):
                module_name = filename[:-3]  # remove .py extension
                module = importlib.import_module(self.directory+"."+module_name, package=None)
                for name in dir(module):
                    if name == module_name:
                        obj = getattr(module, name)
                        if isinstance(obj, type):
                            class_methods = []
                            init_params = []
                            module_hook = getattr(obj, "module_hook", "")
                            if module_hook: #Last bit to make it a valid hooked module
                                for method_name in dir(obj):
                                    method = getattr(obj, method_name)
                                    if callable(method) and not method_name.startswith("__"):
                                        method_description = method.__doc__ or "No description."
                                        try:
                                            sig = inspect.signature(method)
                                        except ValueError:
                                            logging.info("Invalid method, "+method_name)
                                            break
                                        method_args = [param.name for param in sig.parameters.values() if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
                                        class_methods.append({"method_name": method_name, "description": method_description, "args": method_args})
                                if hasattr(obj, '__init__'):
                                    init_sig = inspect.signature(obj.__init__)
                                    init_params = [param.name for param in init_sig.parameters.values() if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and param.name != 'self']
                                class_description = getattr(obj, "description", "No description.")
                                available_modules.append({"class_name": obj.__name__, "description": class_description, "init_params": init_params, "methods": class_methods})
                                if module_hook + "_instances" in globals():
                                    target_instance_list = globals()[module_hook+"_instances"]
                                    # Check if the object is a class and has the same name as the module
                                    if isinstance(obj, type) and obj.__module__ == module.__name__:
                                        # Instantiate the class and append the instance to the array
                                        instance = obj()
                                        target_instance_list.append(instance)
                                        logging.info(f"MODULE LOADED: {module_name} to {module_hook}")
                                    else:
                                        logging.debug(module_name+" failed to load.")
                                else:
                                    logging.debug(module_hook+" module_hook not available.")
                            else:
                                logging.debug("Class "+module_name+" has no module_hook value. Skipped.")
        return_val = json.dumps(available_modules)
        return return_val


    def insert_capabilities_prompt_to_context(self):
        logging.info("Inserting Available Capabilities prompt.")
        ch.add_message_object('user', self.new_capabilities_prompt)

instance = PluginLoader("plugins")