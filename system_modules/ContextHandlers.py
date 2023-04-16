import logging
import datetime
import json
import os


class ContextHandlers:
    description = "A class for handling and managing messages in the chatGPT context object"

    def __init__(self, filename='context.json'):
        self.filename = filename
        self.messages = self.load_context()

    def load_context(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                try:
                    return json.load(f)
                except json.decoder.JSONDecodeError:
                    return []
        else:
            with open(self.filename, 'w') as f:
                json.dump([], f)
            return []

    def save_context(self):
        with open(self.filename, 'w') as f:
            filtered_messages = [msg for msg in self.messages if msg.get('role', '') != 'system']
            json.dump(filtered_messages, f)

    def get_context(self):
        return self.messages

    def get_context_without_timestamp(self):
        messages_without_timestamp = []
        for message in self.messages:
            message_without_timestamp = message.copy()
            del message_without_timestamp['timestamp']
            messages_without_timestamp.append(message_without_timestamp)
        return messages_without_timestamp

    def create_context(self):
        self.messages = []

    def single_message_context(self, role, message):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        return {'role': role, 'timestamp': timestamp, 'content': str(message)}

    def clear_context(self):
        self.create_context()
        self.save_context()

    def add_message_object(self, role, message):
        logging.debug("Adding " + role + " message to context")
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        new_message = {'role': role, 'timestamp': timestamp, 'content': str(message)}
        self.messages.append(new_message)
        self.save_context()
        logging.debug(self.messages)
        
    def add_message_object_at_start(self, role, message):
        logging.debug("Appending " + role + " message at start of context")
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        new_message = {'role': role, 'timestamp': timestamp, 'content': str(message)}
        self.messages.insert(0, new_message)
        self.save_context()
        logging.debug(self.messages)

    def remove_last_message_object(self):
        if self.messages:
            self.messages.pop()
            self.save_context()

    def get_last_message_object(self, user_type=None):
        if user_type:
            for message in reversed(self.messages):
                if message['role'] == user_type:
                    return message
        else:
            if self.messages:
                return self.messages[-1]
        return False

    def replace_last_message_object(self, message, user_type=None):
        if user_type:
            for i in reversed(range(len(self.messages))):
                if self.messages[i]['role'] == user_type:
                    self.messages[i]['content'] = message
                    self.save_context()
                    return
        elif message and self.messages:
            self.messages[-1]['content'] = message
            self.save_context()

    def send_as_type(self, message, type):
        self.messages.append({
            'content': message,
            'role': type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_context()

    def delete_message_at_index(self, index):
        try:
            index = int(index)
            if index < len(self.messages) and index >= 0:
                self.messages.pop(index)
                self.save_context()
                return True
        except ValueError:
            pass
        return False

    def update_message_at_index(self, message, index):
        try:
            index = int(index)
            if index < len(self.messages) and index >= 0:
                self.messages[index]['content'] = message
                self.messages[index]['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.save_context()
        except ValueError:
            pass
        return False


instance = ContextHandlers()
