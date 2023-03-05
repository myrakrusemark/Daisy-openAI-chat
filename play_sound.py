import constants

if not constants.args.no_audio:
    import wave
    import pyaudio
    import threading
    import numpy as np

def play_sound(file, stop_event, thread, volume):
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

def play_sound_with_stop(file, volume=1.0):
    if not constants.args.no_audio:
        stop_event = threading.Event()
        thread = threading.Thread(target=play_sound, args=(file, stop_event, threading.current_thread(), volume))
        thread.start()
        return stop_event, thread