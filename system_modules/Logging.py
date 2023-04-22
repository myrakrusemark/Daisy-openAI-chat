import logging
import sys

class Logging():
    def __init__(self, file_name):
        self.file_name = file_name

    def set_up_logging(self):
        # Create a file handler for the log file
        file_handler = logging.FileHandler(self.file_name)

        # Create a stream handler for stdout
        stream_handler = logging.StreamHandler(sys.stdout)

        # Set the log level for both handlers
        file_handler.setLevel(logging.INFO)
        stream_handler.setLevel(logging.INFO)

        # Create a formatter for the log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(message)s')

        # Set the formatter for both handlers
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # Get the root logger and add the two handlers
        logger = logging.getLogger()
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.CRITICAL)  # Set the root logger level to CRITICAL to turn off all logging
        logger.propagate = False  # Disable propagation to avoid duplicate log messages
        
        # Set up a custom handler for the logging module
        logging.basicConfig(handlers=[file_handler, stream_handler], stream=sys.stdout, encoding='utf-8', level=logging.DEBUG)
