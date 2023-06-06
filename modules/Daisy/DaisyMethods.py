import platform
import logging
import threading
from daisy_llm.Text import print_text
import modules.Porcupine.Porcupine as porcupine
import daisy_llm.ConnectionStatus as cs

cs = cs.ConnectionStatus()

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

def check_internet(awake_stop_event, stop_event, threads):
	awake_stop_event.clear()
	t = threading.Thread(target=cs.check_internet, args=(stop_event, awake_stop_event))
	threads.append(t)
	t.start()		

def wait_for_wake_word_or_input(im, continue_conversation, sound, daisy_stop_event, led=None):
	if led:
		led.turn_on_color(0, 100, 0)  # Solid Green
	awake = [False]
	stop_event = threading.Event()

	# Listen for wake word
	def listen_for_wake_word():
		if continue_conversation and sound:
			awake[0] = True
		else:
			listen_for_daisy_wake(daisy_stop_event, stop_event)
			awake[0] = True

	# Start the wake word thread
	lw_t = threading.Thread(target=listen_for_wake_word, args=())
	lw_t.start()

	# Check for new inputs and wake word
	print_text("Type text or say the wake word: ", "blue")
	while True:
		new_input = im.get_input()
		if new_input is not None:
			# Stop the wake word thread and return the new input
			stop_event.set()
			lw_t.join()
			wake_emote(led)
			return new_input
		elif awake[0]:
			# Return True if the wake word is detected
			wake_emote(led)
			return True
		
		
def wake_emote(led):
	if led:
		led.breathe_color(100, 100, 100)  # Breathe Blue
	print_text("\n٩(ˊ〇ˋ*)و", "pink", "\n\n")