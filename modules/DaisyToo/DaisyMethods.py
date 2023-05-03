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
	result = porcupine_daisy_wake.run(stop_event, awake_stop_event)
	if result:
		print_text("٩(ˊ〇ˋ*)و", "pink", "\n")
	return result


def listen_for_daisy_cancel(stop_event, awake_stop_event):
	result = porcupine_daisy_cancel.run(stop_event, awake_stop_event)
	if result:
		print_text("\n\n(∪｡∪)｡｡｡zzz", "pink", "\n")
		awake_stop_event.set()
	return result