import os
import importlib.util
import json
import inspect

"""
You are Daisy, a chat assistant running on a dedicated device. You have one or more added capabilities available to you that you can use whenever you feel like you need to. Below is a JSON object with a list of classes that you can call. Each class comes with a description, and the methods it contains. This way you know exactly what you can do, so you can work with me to solve problems, look up information, and play games.

[{"class_name": "Calculator", "description": "A plugin for adding or subtracting two numbers.", "init_params": ["first", "second"], "methods": [{"method_name": "add", "description": "Adds two numbers", "args": ["self"]}, {"method_name": "subtract", "description": "Subtracts two number", "args": ["self"]}]}, {"class_name": "GreetingPlugin", "description": "A plugin for greeting people.", "init_params": ["name"], "methods": [{"method_name": "farewell", "description": "Say farewell to the person.", "args": ["self"]}, {"method_name": "greet", "description": "Greet the person.", "args": ["self"]}]}]

When I ask you any question that might require one of your new skills, I would like you to respond in a way that my program can use to trigger the methods available to you. You will receive the output as a response. This is called a "tool former". A tool former is a consistent command that you provide that my code is always watching out for. Here are a few hypothetical examples of calls to classes and their methods. NOTE: These may not be included in the capabilities in the JSON--they are only examples.

user: What is 5+6?
assistant: Calculator[add(5, 6)] #You will never include any text in your tool former response.
user: Response from Calculator: 11
assistant: Five plus six equals eleven.

user: What is the weather in St. Louis right now?
assistant: GoogleWeather[get_weather("St. Louis, MO")]
user: Response from GoogleWeather: 56F, Winds SSW 5mph with gusts reaching 15mph. Partly cloudy all night, clearing by morning.
assistant: Tonight will be chilly, 56 degrees. Be sure to wear a coat because the 15mph winds could make it feel even colder.   

The above are only examples and it is okay that they may not be included in the JSON.   
"""
class PluginLoader:
    def __init__(self, directory):
        self.directory = directory
        self.loaded_classes = []

    def load_classes(self):
        for filename in os.listdir(self.directory):
            if filename.endswith('.py'):
                module_name = filename[:-3]  # remove .py extension
                module_spec = importlib.util.spec_from_file_location(module_name, os.path.join(self.directory, filename))
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type):
                        self.loaded_classes.append(obj)
        return self.loaded_classes



    def get_available_classes_json(self):
        available_classes = []
        for filename in os.listdir(self.directory):
            if filename.endswith('.py'):
                module_name = filename[:-3]  # remove .py extension
                module_spec = importlib.util.spec_from_file_location(module_name, os.path.join(self.directory, filename))
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type):
                        class_methods = []
                        init_params = []
                        for method_name in dir(obj):
                            method = getattr(obj, method_name)
                            if callable(method) and not method_name.startswith("__"):
                                method_description = method.__doc__ or "No description."
                                sig = inspect.signature(method)
                                method_args = [param.name for param in sig.parameters.values() if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
                                class_methods.append({"method_name": method_name, "description": method_description, "args": method_args})
                        if hasattr(obj, '__init__'):
                            init_sig = inspect.signature(obj.__init__)
                            init_params = [param.name for param in init_sig.parameters.values() if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and param.name != 'self']
                        class_description = getattr(obj, "description", "No description.")
                        available_classes.append({"class_name": obj.__name__, "description": class_description, "init_params": init_params, "methods": class_methods})
        return json.dumps(available_classes)


loader = PyFileLoader('plugins')


# Load all instances into a list of objects
#instances = []
#loader.load_classes()

# Print the JSON string of available classes and methods
#print(loader.get_available_classes_json())