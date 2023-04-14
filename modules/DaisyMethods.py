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

	def daisy_cancel(self, stop_event, awake_stop_event):
		# os.environ["CANCEL_LOOP"] = str(self.porcupine_daisy_cancel.run())
		cancel_loop = str(self.porcupine_daisy_cancel.run(stop_event))
		logging.info("<------DAISY CANCEL------>")
		#self.set_cancel_loop(cancel_loop)
		awake_stop_event.set()
		return 


	def set_cancel_loop(self, boolean):

		try:
			self.cancel_loop = boolean
		except Exception as e:
			logging.error("Error daisy_set_cancel_loop: %s", e)

		return self.cancel_loop

instance = DaisyMethods()
