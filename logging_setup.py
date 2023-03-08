import logging
import sys

# Create a file handler for the log file
file_handler = logging.FileHandler('daisy.log')

# Create a stream handler for stdout
stream_handler = logging.StreamHandler(sys.stdout)

# Set the log level for both handlers
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.DEBUG)

# Create a formatter for the log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set the formatter for both handlers
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Get the root logger and add the two handlers
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Log some messages
logging.debug('This is a debug message')
logging.info('This is an info message')
logging.warning('This is a warning message')
logging.error('This is an error message')
logging.critical('This is a critical message')
