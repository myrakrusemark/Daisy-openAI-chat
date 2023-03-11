import os
from plugins import constants
import pygame
import threading
#from pynput import keyboard
import time
import logging
import numpy as np
from io import BytesIO

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
        sound = ""
        if isinstance(name_or_path, BytesIO):
            logging.debug(f"Playing BytesIO with volume {volume}")

            sound = pygame.mixer.music.load(name_or_path)
            pygame.mixer.music.play()

            # Wait for the music to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)  # Wait for 100 milliseconds before checking again
        else:
            logging.debug(f"Playing sound {name_or_path} with volume {volume}")

            # Load sound from dictionary
            sound = self.sounds.get(name_or_path)
            sound.set_volume(volume)
            sound.play()

            # Define function to stop playback when escape key is pressed or stop_event is set
            event = threading.Event()

            # Set the currently playing sound
            self.current_sound = sound

            # Wait for the sound to finish playing or the escape key/stop_event to be pressed
            sound_length = sound.get_length()
            while not event.is_set() and sound_length > 0:
                event.wait(min(sound_length, 0.1))  # Wait for the event to be set or the timeout to expire
                sound_length -= 0.1  # Subtract the time waited from the remaining sound length

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
