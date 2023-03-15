import multiprocessing as mp

from flask import Flask, render_template
from flask_bootstrap import Bootstrap


class WebConfig:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that serves a web page."
    module_hook = "Main_start"

    def __init__(self):
        self.shared_data = []
        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.home)

        
    def home(self):
        return self.shared_data[0]
    
    def main(self, shared_data):
        self.shared_data = list(shared_data)
        self.app.run()

#if __name__ == '__main__':
#    myapp = WebConfig()
#    myapp.run()