import os
import sys
from django.core.management import execute_from_command_line
import threading
from wsgiref.simple_server import WSGIRequestHandler


class WebConfigDjango:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that serves a web page."
    module_hook = "Main_start"

    def __init__(self, settings_module="modules.WebConfigDjango.core.settings"):
        self.settings_module = settings_module
        self.server = None
        self.stop_event = threading.Event()

    def close(self):
        self.stop_event.set()
        if self.server:
            self.server.shutdown()

    def main(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", self.settings_module)
        argv = ['modules/WebConfigDjango/manage.py', 'runserver', '--noreload']
        handler = WSGIRequestHandler
        self.server = execute_from_command_line(argv)
