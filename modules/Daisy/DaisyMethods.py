import platform
import logging
from daisy_llm.Text import print_text
import modules.Porcupine.Porcupine as porcupine

cancel_loop = False

#Instantiate ("daisy cancel") wake word
keyword_paths = None
if platform.system() == "Windows":
	keyword_paths = ["modules/Porcupine/porcupine_models/daisy-cancel_en_windows_v2_1_0.ppn"]
elif platform.system() == "Linux":
	keyword_paths = ["modules/Porcupine/porcupine_models/daisy-cancel_en_raspberry-pi_v2_1_0.ppn"]
else:
	logging.error("Unknown operating system, can't load wake word model.")

porcupine_daisy_cancel = porcupine.Porcupine(
				keyword_paths=keyword_paths,
				sensitivities=[0.5])

#Instantiate ("hey daisy") wake word
keyword_paths = None
if platform.system() == "Windows":
	keyword_paths = ["modules/Porcupine/porcupine_models/daisy-daisy_en_windows_v2_1_0.ppn", "modules/Porcupine/porcupine_models/hey-daisy_en_windows_v2_1_0.ppn"]
elif platform.system() == "Linux":
	keyword_paths = ["modules/Porcupine/porcupine_models/daisy-daisy_en_raspberry-pi_v2_1_0.ppn", "modules/Porcupine/porcupine_models/hey-daisy_en_raspberry-pi_v2_1_0.ppn"]
else:
	logging.error("Unknown operating system, can't load wake word model.")

porcupine_daisy_wake = porcupine.Porcupine(
				keyword_paths=keyword_paths,
				sensitivities=[0.5, 0.5])

def listen_for_daisy_wake(stop_event, awake_stop_event):
	awake_stop_event.clear()
	porcupine_daisy_wake.run(stop_event, awake_stop_event)


def listen_for_daisy_cancel(stop_event, awake_stop_event):
	porcupine_daisy_cancel.run(stop_event, awake_stop_event)
	awake_stop_event.set()

