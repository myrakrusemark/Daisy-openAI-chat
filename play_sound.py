import constants

if not constants.args.no_audio:
    import wave
    import pyaudio
    import threading
    import numpy as np
    from mutagen.mp3 import MP3
    import pygame

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

def play_mpeg(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    # Wait until music has finished playing
    while pygame.mixer.music.get_busy():
        continue

    pygame.mixer.music.stop()

def play_sound_with_stop(file, volume=1.0, type="wave"):
    print("Audio file: "+file)
    if not constants.args.no_audio:
        stop_event = threading.Event()
        if type=="wave":
            thread = threading.Thread(target=play_wave, args=(file, stop_event, threading.current_thread(), volume))
        if type=="mpeg":
            thread = threading.Thread(target=play_mpeg, args=(file,))

        thread.start()
        return stop_event, thread