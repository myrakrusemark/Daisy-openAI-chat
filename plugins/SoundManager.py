import os
from plugins import constants
import pygame
import threading
#from pynput import keyboard
import time
import logging
import numpy as np

# Set the DISPLAY environment variable for pynput
#os.environ['DISPLAY'] = ':0'

pygame.init()

class SoundManager:
    description = "A class for managing sound files in a directory, playing sounds, and stopping playback."
    def __init__(self, directory):
        """
        A class for managing sound files in a directory.

        :param directory: The directory containing sound files.
        """
        self.directory = directory
        self.sounds = {}

        # Load all sound files in the directory
        for filename in os.listdir(directory):
            if filename.endswith('.wav') or filename.endswith('.mp3'):
                # Extract filename without extension
                name = os.path.splitext(filename)[0]

                # Load sound file and store in dictionary
                path = os.path.join(directory, filename)
                try:
                    sound = pygame.mixer.Sound(path)
                    self.sounds[name] = sound
                except pygame.error:
                    logging.warning(f"Failed to load sound file '{filename}'")

        self.current_sound = None

    # Function to play MPEG files
    def play_sound(self, name_or_path, volume=1, stop_event=None):
        """Function to play sound files and define function to stop playback when escape key is pressed or stop_event is set."""
        if os.path.isfile(name_or_path):
            # Load sound from file
            sound = pygame.mixer.Sound(name_or_path)
        else:
            # Load sound from dictionary
            sound = self.sounds.get(name_or_path)

        logging.debug(f"Playing sound {name_or_path} with volume {volume}")

        # Define function to stop playback when escape key is pressed or stop_event is set
        event = threading.Event()

        """key_not_pressed = True
        def on_press(key):
            nonlocal key_not_pressed
            if key == keyboard.Key.esc:
                # Stop the playback
                logging.debug("Sound stopped")
                sound.stop()
                key_not_pressed = False
                event.set()  # Set the event to signal the main thread to stop waiting
                return False  # Stop the listener
            elif stop_event and stop_event.is_set():
                # Stop the playback
                logging.debug("Sound stopped by stop_event")
                sound.stop()
                key_not_pressed = False
                event.set()  # Set the event to signal the main thread to stop waiting
                return False  # Stop the listener
        """

        # Play the sound object
        sound.set_volume(1)
        sound.play()


        # Set the currently playing sound
        self.current_sound = sound

        # Wait for the sound to finish playing or the escape key/stop_event to be pressed
        sound_length = sound.get_length()
        #with keyboard.Listener(on_press=on_press) as listener:
        while not event.is_set() and sound_length > 0:
            event.wait(min(sound_length, 0.1))  # Wait for the event to be set or the timeout to expire
            sound_length -= 0.1  # Subtract the time waited from the remaining sound length
        #if listener.running and key_not_pressed:
         #   listener.stop()

        logging.debug(f"Playback of sound {name_or_path} completed")

        return sound

    # Function to play audio files with a thread
    def play_sound_with_thread(self, name, volume=1.0):
        """Function to play audio files with a thread and return a stop event and thread object."""
        stop_event = threading.Event()
        thread = threading.Thread(target=self.play_sound, args=(name, volume, stop_event))

        # Start the sound playback thread
        logging.debug(f"Starting threaded playback of file {name}.wav")
        thread.start()

        return stop_event, thread

    def stop_playing(self):
        """Function to stop the current sound playback."""
        if self.current_sound:
            self.current_sound.stop()
