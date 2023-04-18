import os
import platform
import pvporcupine
import logging

import modules.Porcupine.Porcupine as porcupine


class DaisyMethods:
	description = "Methods used for control and monitoring of the main Daisy class. Mostly to prevent circular imports."


	def __init__(self):

		self.cancel_loop = False
		
		#Instantiate ("daisy cancel") wake word
		keyword_paths = None
		if platform.system() == "Windows":
			keyword_paths = ["modules/Porcupine/porcupine_models/daisy-cancel_en_windows_v2_1_0.ppn"]
		elif platform.system() == "Linux":
			keyword_paths = ["modules/Porcupine/porcupine_models/daisy-cancel_en_raspberry-pi_v2_1_0.ppn"]
		else:
			logging.error("Unknown operating system, can't load wake word model.")

		self.porcupine_daisy_cancel = porcupine.Porcupine(
						keyword_paths=keyword_paths,
						sensitivities=[0.5])
		
		keyword_paths = None
		if platform.system() == "Windows":
			keyword_paths = ["modules/Porcupine/porcupine_models/daisy-daisy_en_windows_v2_1_0.ppn", "modules/Porcupine/porcupine_models/hey-daisy_en_windows_v2_1_0.ppn"]
		elif platform.system() == "Linux":
			keyword_paths = ["modules/Porcupine/porcupine_models/daisy-daisy_en_raspberry-pi_v2_1_0.ppn", "modules/Porcupine/porcupine_models/hey-daisy_en_raspberry-pi_v2_1_0.ppn"]
		else:
			logging.error("Unknown operating system, can't load wake word model.")

		self.porcupine_daisy_wake = porcupine.Porcupine(
						keyword_paths=keyword_paths,
						sensitivities=[0.5, 0.5])

	def listen_for_daisy_wake(self, stop_event, awake_stop_event):
		awake_stop_event.clear()
		return self.porcupine_daisy_wake.run(stop_event, awake_stop_event)
	
	def listen_for_daisy_cancel(self, stop_event, awake_stop_event):
		self.porcupine_daisy_cancel.run(stop_event, awake_stop_event)
		logging.info("<------DAISY CANCEL------>")
		awake_stop_event.set()
		return 


	def set_cancel_loop(self, boolean):

		try:
			self.cancel_loop = boolean
		except Exception as e:
			logging.error("Error daisy_set_cancel_loop: %s", e)

		return self.cancel_loop

instance = DaisyMethods()
