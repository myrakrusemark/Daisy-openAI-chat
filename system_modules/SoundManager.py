import os
from io import BytesIO
import logging
import threading
import pydub
from pydub import AudioSegment
from pydub.effects import speedup
import simpleaudio
import numpy as np

class SoundManager:
    description = "A class for managing sound files in a directory, playing sounds, and stopping playback."
    
    def __init__(self, directory='sounds/'):
        self.directory = directory
        self.sounds = {}
        self.current_sound = None
        self.playback = None

        # Load all sound files in the directory
        for filename in os.listdir(directory):
            if filename.endswith('.wav') or filename.endswith('.mp3'):
                # Extract filename without extension
                name = os.path.splitext(filename)[0]

                # Load sound file and store in dictionary
                path = os.path.join(directory, filename)
                try:
                    sound = pydub.AudioSegment.from_file(path)
                    self.sounds[name] = sound
                except pydub.exceptions.CouldntDecodeError:
                    logging.warning(f"Failed to load sound file '{filename}'")


    def play_sound(self, name_or_bytes, volume=1.0, stop_event=None, sound_stop_event=None, speed=1.0):
        logging.debug("play_sound")
        if isinstance(name_or_bytes, bytes):
            sound = AudioSegment.from_file(BytesIO(name_or_bytes))
        elif isinstance(name_or_bytes, str):
            sound = self.sounds.get(name_or_bytes)
            if sound is None:
                raise ValueError(f"No sound named {name_or_bytes}")
        else:
            raise TypeError(f"Unsupported argument type {type(name_or_bytes)}")

        self.current_sound = sound

        if stop_event is None:
            stop_event = threading.Event()

        # adjust the playback speed of the sound
        if speed != 1.0:
            sound = speedup(sound, speed)

        # create a new thread to play the sound
        self._play_sound_method(sound, volume, stop_event, sound_stop_event)

        self.current_sound = None
        return True
    

    def _play_sound_method(self, sound, volume=1.0, stop_event=None, sound_stop_event=None):
        logging.debug("_play_sound_method")
        # Adjust volume
        scaled_volume = volume * 32767
        sound_array = sound.get_array_of_samples()
        scaled_array = np.round(scaled_volume * np.array(sound_array) / 32767).astype(np.int16)
        sound = sound._spawn(scaled_array)

        # Convert audio segment to raw audio data
        raw_data = sound.raw_data

        # Set audio parameters
        num_channels = sound.channels
        bytes_per_sample = sound.sample_width
        sample_rate = sound.frame_rate

        # Play audio using simpleaudio
        self.playback = simpleaudio.play_buffer(raw_data, num_channels=num_channels, bytes_per_sample=bytes_per_sample, sample_rate=sample_rate)

        # Loop until either stop_event or sound_stop_event is set
        while True:
            if stop_event:
                if stop_event.is_set():
                    # Stop the playback if the stop_event is set
                    self.playback.stop()
                    return False
            if sound_stop_event:
                if sound_stop_event.is_set():
                    # Stop the playback if the sound_stop_event is set
                    self.playback.stop()
                    return True

            # Check if the playback has finished
            if not self.playback.is_playing():
                return True



    def play_sound_with_thread(self, name_or_bytes, volume=1.0, awake_stop_event=None, sound_stop_event=None):
        logging.debug("play_sound_with_thread")
        thread = threading.Thread(target=self.play_sound, args=(name_or_bytes, volume, awake_stop_event, sound_stop_event))
        thread.start()


