import platform
import subprocess
import threading
import logging
import time

class ConnectionStatus(threading.Thread):
    description = "A class that checks the status of internet connectivity."


    def __init__(self):
        self.is_connected = False



    def check_internet(self, stop_event, awake_stop_event):
        """Creates and starts a new CheckInternetThread instance, waits for it to complete or timeout, and returns a boolean value indicating if internet connectivity is available."""

        while not stop_event.is_set():
            try:
                # Ping google.com and check if we receive any response
                logging.debug('Pinging google.com')

                if platform.system() == 'Windows':
                    subprocess.check_output(['ping', '-n', '1', 'google.com'], stderr=subprocess.PIPE)
                
                else:
                    subprocess.check_output(['ping', '-c', '1', 'google.com'], stderr=subprocess.PIPE)
                self.is_connected = True

                # Log a message to indicate that the Internet is available
                logging.debug('Internet connection is available')

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                self.is_connected = False

                # Log a warning message to indicate that the Internet is not available
                logging.debug('Internet connection is not available')
            except Exception as e:
                # general exception handling
                logging.exception(e)

            # Check if the thread is connected and cancel the loop if it is
            if not self.is_connected:
                awake_stop_event.set()
                logging.error("No Internet connection.")
            else:
                awake_stop_event.clear()
                logging.debug("Internet connection available.")
        
            time.sleep(1)


