import platform
import subprocess
import threading
import logging

class ConnectionStatus(threading.Thread):
    description = "A class that checks the status of internet connectivity."

    # Check if Internet is available
    class CheckInternetThread(threading.Thread):
        description = "A nested class that checks for internet connectivity by pinging Google."

        def __init__(self):
            threading.Thread.__init__(self)
            self.is_connected = False

        def run(self):
            """Method of CheckInternetThread that is executed when the thread starts; pings Google to check for internet connectivity and logs a message."""
            try:
                # Ping google.com and check if we receive any response
                logging.debug('Pinging google.com')

                if platform.system() == 'Windows':
                    output = subprocess.check_output(['ping', '-n', '1', 'google.com'], stderr=subprocess.PIPE)
                else:
                    output = subprocess.check_output(['ping', '-c', '1', 'google.com'], stderr=subprocess.PIPE)
                self.is_connected = True

                # Log a message to indicate that the Internet is available
                logging.debug('Internet connection is available')

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                self.is_connected = False

                # Log a warning message to indicate that the Internet is not available
                logging.debug('Internet connection is not available')


    def check_internet(self):
        """Creates and starts a new CheckInternetThread instance, waits for it to complete or timeout, and returns a boolean value indicating if internet connectivity is available."""

        # Create a new thread to check for internet connectivity
        thread = self.CheckInternetThread()
        thread.start()

        # Wait for the thread to complete or timeout after 5 seconds
        # This prevents the function from blocking indefinitely
        thread.join(timeout=5)

        # Check if the thread is connected and return the result
        is_connected = thread.is_connected
        return is_connected

instance = ConnectionStatus()