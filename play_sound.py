import constants
import keyboard

if not constants.args.no_audio:
    import wave
    import pyaudio
    import threading
    import numpy as np
    import pygame
    import mutagen.mp3

    pygame.init()
"""
#I think this function plays sound faster than pygame but it will need some testing.
def play_wave(file, stop_event, thread, volume):
    wf = wave.open(file, 'rb')
    audio = pyaudio.PyAudio()

    # Open a new audio stream for playback
    stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

    # Continuously read data from the audio file and write it to the audio stream
    data = wf.readframes(1024)
    while data and not stop_event.is_set():
        # Convert the raw audio data to a numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Scale the audio data by the volume factor
        scaled_data = (audio_data * volume).astype(np.int16)

        # Write the scaled audio data to the stream
        stream.write(scaled_data.tobytes())

        # Read the next block of audio data
        data = wf.readframes(1024)

    # Cleanup the audio stream and audio object
    stream.stop_stream()
    stream.close()
    audio.terminate()
    thread.join()
"""
#MPEG playback required for TTS files
def play_mpeg(file_path):

    if not file_path.endswith(".wav"):
        mp3 = mutagen.mp3.MP3(file_path)
        pygame.mixer.init(frequency=mp3.info.sample_rate) #Match sample rate. On Raspberry Pi, the TTS files play too slow.

    pygame.mixer.music.load(file_path)
    pygame.mixer.music.set_volume(constants.args.volume)
    pygame.mixer.music.play()

    # Wait until music has finished playing
    while pygame.mixer.music.get_busy():
        #If user pressed ESC, stop TTS playback (will incorporate GPIO button)
        #There is no de-bouncing of the key, so it will quickly stop playback of all audio files in the list of file_paths. That's fine for now.
        if not constants.args.hardware_mode:
            if keyboard.is_pressed("esc") or constants.stop_sound:
                # Do something when the ESC key is pressed
                print("Sound stopped")
                constants.stop_sound = False
                break  # Exit the loop when the ESC key is pressed
        continue

    pygame.mixer.music.stop()

    return pygame.mixer.music



def play_sound_with_thread(file, volume=1.0):
    if not constants.args.no_audio:
        stop_event = threading.Event()
        thread = threading.Thread(target=play_mpeg, args=(file,))

        # Start the sound playback thread
        thread.start()

        return stop_event, thread
        