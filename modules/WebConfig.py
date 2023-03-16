import multiprocessing as mp
import subprocess

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
        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.home)

        
    def home(self):
        return
    
    def main(self, shared_data=[]):
        sd = list(shared_data)
        print("Shared data value in subprocess:", shared_data["value"])
        self.app.run()

#if __name__ == '__main__':
#    myapp = WebConfig()
#    myapp.run()