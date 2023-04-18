import logging
from importlib import import_module
import os
from django.conf import settings
from django.urls import path
import inspect
from . import views

urlpatterns = [
    #path('', views.index, name='index'),
]




def load_module_routes():
    logging.info("Loading module routes...")

    try:
        modules_folder = "modules"
        modules = [m for m in os.listdir(modules_folder) if os.path.isdir(os.path.join(modules_folder, m))]

        for module_name in modules:
            module_path = f"{modules_folder}.{module_name}"
            logging.debug(f"Importing URLs and views from module: {module_name}")

            try:
                urls_module = import_module(f"{module_path}.urls")
                views_module = import_module(f"{module_path}.views")

                #Run __init__() method for views.py
                class_name = None
                class_obj = None
                for attr_name in dir(views_module):
                    attr = getattr(views_module, attr_name)
                    if inspect.isclass(attr):
                        class_name = attr_name
                        class_obj = attr
                        break

                if hasattr(views_module, class_name):
                    logging.info(f"Running __init__() method for class: {class_name}")
                    class_obj = getattr(views_module, class_name)
                    instance = class_obj()  # create an instance of the class
                    instance.__init__()

            except ModuleNotFoundError:
                logging.debug(f"Skipping module {module_name}: urls.py or views.py not found")
                continue

            if hasattr(urls_module, "urlpatterns"):



                try:
                    module = import_module(module_path)
                except ModuleNotFoundError:
                    logging.debug(f"Skipping module {module_name}: module not found")
                    continue

                if hasattr(module, "__init__"):
                    logging.info(f"Running __init__() method for module: {module_name}")
                    module.__init__("modules.Dashboard_WebConfigDjango.views.Dashboard(TemplateView)")



                new_urlpatterns = getattr(urls_module, "urlpatterns")
            else:
                new_urlpatterns = []


            for view_name in dir(views_module):
                view = getattr(views_module, view_name)
                if hasattr(view, "route_path"):
                    route_path = getattr(view, "route_path")
                    logging.info(f"Adding route: {route_path} for view: {view_name}")

                    # Use as_view() if available, otherwise use the view class
                    view_func = getattr(view, "as_view", lambda: view)()
                    new_urlpatterns.append(path(route_path, view_func))

            # Add default template folder to the app
            templates_folder = os.path.join(settings.BASE_DIR, modules_folder, module_name, "templates")
            if os.path.exists(templates_folder):
                app_template_dir = os.path.join(module_name, "templates")
                if app_template_dir not in settings.TEMPLATES[0]["APP_DIRS"]:
                    settings.TEMPLATES[0]["APP_DIRS"].append(app_template_dir)
                    logging.info(f"Adding templates folder: {templates_folder} for module: {module_name}")

            # Add the URLs to Django's main urlpatterns
            if new_urlpatterns:
                from django.urls import include
                urlpatterns.append(path("", include(new_urlpatterns)))
                logging.info(f"Added {len(new_urlpatterns)} routes from module: {module_name}")

            logging.debug("URLS: " + str(new_urlpatterns))

    except Exception as e:
        logging.error(f"Error loading module routes: {e}")


# Load additional routes from modules
load_module_routes()