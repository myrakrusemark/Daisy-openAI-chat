import os
from modules import constants
import pygame
import threading
#from pynput import keyboard
import time
import logging
import numpy as np
from io import BytesIO

import modules.DaisyMethods as dm 


class SoundManager:
    description = "A class for managing sound files in a directory, playing sounds, and stopping playback."
    def __init__(self, directory):
        self.directory = directory
        self.sounds = {}
        self.current_sound = None
        self.dm = dm.instance

        pygame.init()

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

    # Function to play sound files (MP3 or WAV)
    def play_sound(self, name_or_bytes, volume=1, stop_event=None):
        """Function to play sound files and define function to stop playback when escape key is pressed or stop_event is set."""
        sound = ""
        if isinstance(name_or_bytes, BytesIO):
            logging.debug(f"Playing BytesIO with volume {volume}")

            sound = pygame.mixer.music.load(name_or_bytes)
            pygame.mixer.init(44100, -16, 1, 1024)
            pygame.mixer.music.play()

            # Wait for the music to finish playing
            while pygame.mixer.music.get_busy():
                #If cancel keyword (Daisy cancel)
                #if os.environ["CANCEL_LOOP"] == "True":
                if self.dm.get_cancel_loop():
                    pygame.mixer.music.stop()
                    break
                pygame.time.wait(100)  # Wait for 100 milliseconds before checking again
        else:
            logging.debug(f"Playing sound {name_or_bytes} with volume {volume}")

            # Load sound from dictionary
            sound = self.sounds.get(name_or_bytes)
            sound.set_volume(volume)
            sound.play()

            # Define function to stop playback when stop_event is set
            event = threading.Event()

            # Set the currently playing sound
            self.current_sound = sound

            # Wait for the sound to finish playing
            sound_length = sound.get_length()
            while not event.is_set() and sound_length > 0:

                #If cancel keyword (Daisy cancel)
                    #Not putting this here right now because setting cancel_loop to True immediately cancels playback of the "end" sound

                event.wait(min(sound_length, 0.1))  # Wait for the event to be set or the timeout to expire
                sound_length -= 0.1  # Subtract the time waited from the remaining sound length

        logging.debug(f"Playback of sound {name_or_bytes} completed")

        return sound

    # Function to play audio files with a thread
    def play_sound_with_thread(self, name, volume=1.0):
        """Function to play audio files with a thread and return a stop event and thread object."""
        stop_event = threading.Event()
        play_sound_thread = threading.Thread(target=self.play_sound, args=(name, volume, stop_event))

        # Start the sound playback thread
        logging.debug(f"Starting threaded playback of file {name}.wav")
        play_sound_thread.start()

        return stop_event, play_sound_thread

    def stop_playing(self):
        """Function to stop the current sound playback."""
        if self.current_sound:
            self.current_sound.stop()

instance = SoundManager('sounds/')