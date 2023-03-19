import threading
import signal


from flask import Flask, render_template, jsonify

class WebConfig:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A module that serves a web page."
    module_hook = "Main_start"

    @staticmethod
    def main(stop_event):
        print("WEBCONFIG STARTED!")
        stop_event = threading.Event()  # Create an Event object to signal the loop to stop

        import ModuleLoader as ml

        import modules.ContextHandlers as ch
        print(ml.instance.available_modules_json)

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

        try:
            app.run(host='0.0.0.0', port=5000)
        except KeyboardInterrupt:
            stop_event.set()

instance = WebConfig()
