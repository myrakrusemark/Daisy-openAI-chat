#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.core.management import execute_from_command_line


class WebConfigDjango:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that serves a web page."
    module_hook = "Main_start"

    def __init__(self, settings_module="modules.WebConfigDjango.core.settings"):
        self.settings_module = settings_module

    def main(self, stop_event):        
        self.execute_command("runserver")

    def execute_command(self, command):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", self.settings_module)
        argv = ['modules/WebConfigDjango/manage.py', 'runserver', '--noreload']
        execute_from_command_line(argv)

