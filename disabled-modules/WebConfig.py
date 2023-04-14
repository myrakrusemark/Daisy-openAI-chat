from flask import Flask, render_template, jsonify, json, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import system_modules.ContextHandlers as ch
import logging
import importlib
import pkgutil

class WebConfig:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that serves a web page."
    module_hook = "Main_start"

    def __init__(self):
        self.ch = ch.instance

        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.abspath(__file__))
        self.app.secret_key = 'secret'

        @self.app.route('/')
        def home():
            return render_template('index.html')

        @self.app.route('/chat_data')
        def _chat_data():
            context = self.ch.messages
            return jsonify(context)

        @self.app.route('/chat')
        def chat():
            context = self.ch.messages
            return render_template('chat.html', messages=context)

        @self.app.route('/send_message', methods=['POST'])
        def _send_message():
            try:
                message = request.json
                print("Add MESSAGE TO CONTEXT")
                print(message)
                self.ch.add_message_object(message['role'], message['content'])
                return jsonify({'status': 'success', 'message': message})
            except Exception as e:
                print(e)
                return jsonify({'status': 'error', 'message': str(e)})


        @self.app.route('/modules')
        def modules():
            modules_data_json = ml.instance.available_modules_json
            modules_data = json.loads(modules_data_json)
            return render_template('modules.html', modules_data=modules_data)

        @self.app.route('/routes')
        def _routes():
            routes = []
            for rule in self.app.url_map.iter_rules():
                # Skip static files and other non-GET routes
                if not str(rule).startswith('/static') and 'GET' in rule.methods:
                    # Exclude routes with names starting with an underscore
                    if not rule.endpoint.startswith('_'):
                        routes.append({ 'path': str(rule), 'name': str(rule.endpoint) })
            return jsonify(routes)

        @self.app.route('/upload', methods=['GET', 'POST'])
        def _upload_file():
            if request.method == 'POST':
                # check if the post request has the file part
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                file = request.files['file']
                # if user does not select file, browser also
                # submit an empty part without filename
                if file.filename == '':
                    flash('No selected file')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    flash('File uploaded successfully')
                    return redirect(url_for('modules'))
                else:
                    flash('File must be a .py file')
                    return redirect(request.url)
            return render_template('add_module.html')

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in {'py'}


    def load_module_routes(self):
        # HOOK: WebConfig_add_routes
        logging.info("Loading module routes...")
        try:
            import ModuleLoader as ml
            hook_instances = ml.instance.hook_instances
            if "WebConfig_add_routes" in hook_instances:
                WebConfig_add_routes_instances = hook_instances["WebConfig_add_routes"]
                for instance in WebConfig_add_routes_instances:
                    module_name = type(instance).__name__
                    logging.info("Adding routes to WebConfig from " + module_name)

                    # Discover modules within the 'modules' package and its subpackages
                    modules = []
                    for loader, name, is_pkg in pkgutil.walk_packages(['modules'], prefix='modules.'):
                        if not is_pkg:
                            modules.append(name)

                    # Import the module dynamically
                    for module in modules:
                        if module.endswith(module_name):
                            my_class = getattr(importlib.import_module(module), module_name)()

                            for method_name in dir(my_class):
                                method = getattr(my_class, method_name)
                                if hasattr(method, 'is_route') and method.is_route:
                                    logging.info("Adding " + method.route_path)
                                    self.app.route(method.route_path)(method)
            else:
                raise logging.info("No WebConfig_add_routes module found.")

        except Exception as e:
            logging.error(f'Error loading module routes: {e}')

    def start_app(self):
        #self.load_module_routes()
        self.app.run(host='0.0.0.0', port=5000)

    @staticmethod
    def main(stop_event):
        try:
            #instance = WebConfig()
            instance.load_module_routes()
            instance.start_app()
        except Exception as e:
            print(f"Error starting web app: {e}")

instance = WebConfig()
