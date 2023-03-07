import constants
import os

# Set the DISPLAY environment variable for pynput
os.environ['DISPLAY'] = ':0'
from pynput import keyboard

if not constants.args.no_audio:
    import wave
    import pyaudio
    import threading
    import numpy as np
    import pygame
    import mutagen.mp3

    pygame.init()


#MPEG playback required for TTS files
def play_mpeg(file_path, volume=1):

    key_not_pressed = True
    def on_press(key):
        if key == keyboard.Key.esc:
            # Do something when the ESC key is pressed
            print("Sound stopped")
            pygame.mixer.music.stop()            
            return False  # Stop the listener


    if not file_path.endswith(".wav"):
        mp3 = mutagen.mp3.MP3(file_path)
        pygame.mixer.init(frequency=mp3.info.sample_rate) #Match sample rate. On Raspberry Pi, the TTS files play too slow.

    pygame.mixer.music.load(file_path)
    pygame.mixer.music.set_volume(constants.args.volume*volume)
    pygame.mixer.music.play()

    # Listen for the Escape key
    with keyboard.Listener(on_press=on_press) as listener:
        # Wait until music has finished playing
        while pygame.mixer.music.get_busy() and listener.running:
            continue


    pygame.mixer.music.stop()

    return pygame.mixer.music



def play_sound_with_thread(file, volume=1.0):
    if not constants.args.no_audio:
        stop_event = threading.Event()
        thread = threading.Thread(target=play_mpeg, args=(file,volume))

        # Start the sound playback thread
        thread.start()

        return stop_event, thread
        