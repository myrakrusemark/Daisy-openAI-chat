import signal
import sys
import logging

class SignalHandlers():
	description = "A class that defines signal handlers for system signals, specifically Ctrl+C which will exit the program and log a message."

	def signal_handler(self, sig, frame):
		"""A method that logs an informational message and exits the program when a specified signal (sig) is received. In this case, it's the Ctrl+C signal."""
		logging.info('Ctrl+C: Exiting Program...')
		sys.exit(0)