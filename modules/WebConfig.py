from flask import Flask, render_template, jsonify

import ModuleLoader as ml
import modules.ContextHandlers as ch

class WebConfig:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that serves a web page."
    module_hook = "Main_start"

    def start_app(self):
        app = Flask(__name__)

        @app.route('/')
        def hello():
            return render_template('index.html')

        @app.route('/modules')
        def modules():
            modules_data = ml.instance.available_modules_json
            return jsonify(modules_data)

        @app.route('/chat_data')
        def chat_data():
            context = ch.instance.messages
            return jsonify(context)

        @app.route('/chat')
        def chat():
            context = ch.instance.messages
            return render_template('chat.html', messages=context)

        app.run(host='0.0.0.0', port=5000)

    @staticmethod
    def main(stop_event):
        try:
            instance = WebConfig()
            instance.start_app()
        except Exception as e:
            print(f"Error starting web app: {e}")

instance = WebConfig()
