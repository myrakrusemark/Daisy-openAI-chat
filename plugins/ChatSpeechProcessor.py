import speech_recognition as sr
import pyaudio
import websockets
import asyncio
import base64
import json
import threading
import time
from plugins import constants
import sys
import os
import re
import string
from dotenv import load_dotenv
import pyttsx3
import requests
import io
import tempfile
import logging


load_dotenv()

#Initialize available sound effects
from plugins import SoundManager
sounds = SoundManager.SoundManager('sounds/')



#Init fallback TTS and set voice
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', "english-us")

class ChatSpeechProcessor:
    description = "A class that handles speech recognition and text-to-speech processing for a chatbot."
    def __init__(self):
        # Set up AssemblyAI API key and websocket endpoint
        self.auth_key = "f7754f3d71ac422caf4cfc54bace4306"
        self.uri = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

        # Define global variables
        self.result_str = ""
        self.new_result_str = ""
        self.result_received = False
        self.api_key = os.environ["AAI_KEY"]



        self.r = sr.Recognizer()


    def listen_for_wake_word(self):          
        """Listens for a wake word and returns True if detected."""

        with sr.Microphone() as source:
            try:
                self.r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening
                logging.info(f"Waiting for wake word: '{constants.wake_word}'")
                audio = self.r.listen(source)
            except sr.WaitTimeoutError:
                logging.error("Timeout occurred while waiting for wake word.")
                return False
            
            try:
                logging.info("Recognizing...")
                text = self.r.recognize_google(audio)
                text = text.lower()
                logging.info(f"Recognized text: {text}")
                       
            except Exception as error:
                logging.error(f"Could not understand: {error}")
                return False

        #Enable the ability to exit the program in a keyboard blocking state
        exit_string = self.remove_non_alpha(text.lower())
        if exit_string == "exitprogram":
            logging.info("Exiting program...")
            sys.exit(0)

        if text in constants.similar_wake_words:
            sounds.play_sound_with_thread('alert')
            logging.info("Wake word detected.")
            return True
        
    def tts(self, text):
        """Converts text to speech using Google TTS or a fallback TTS engine."""
        text_parts = self.split_text_for_google_tts(text)
        file_paths = []

        # Request multiple text parts and save to multiple temp files
        for text in text_parts:
            url = "http://translate.google.com/translate_tts"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            params = {"q": self.remove_non_alphanumeric(text),
                        "ie": "UTF-8",
                        "client": "tw-ob",
                        "tl": "en"}

            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()  # Raise an exception for non-2xx response codes

                # Read the audio data from the response object
                audio_data = io.BytesIO(response.content)
            except requests.exceptions.RequestException as error:
                # Log the error message instead of printing it to stdout
                logging.error(f'RequestException: {error}')
                break


            # Save the contents of the BytesIO object to a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(audio_data.getvalue())
                file_path = tmp_file.name
                file_paths.append(file_path)  # Add the file path to the list

        # Play each file in sequence
        for file_path in file_paths:
            sounds.play_sound(file_path, 1)

        # If Google TTS somehow fails, fallback to local TTS
        #except Exception as e:
            # Log the error message instead of printing it to stdout
        #    logging.error(f'Exception: {e}')
        #    engine.say(text)
        #    engine.runAndWait()  

    async def stt_send_receive(self):
        """Sends audio data to AssemblyAI STT API and receives text transcription in real time using websockets."""

        # Set up PyAudio
        FRAMES_PER_BUFFER = 3200
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER
        )

        async with websockets.connect(
            self.uri,
            extra_headers=(("Authorization", self.api_key),),
            ping_interval=5,
            ping_timeout=20
        ) as _ws:
            await asyncio.sleep(0.1)
            logging.info("Receiving SessionBegins ...")
            session_begins = await _ws.recv()
            logging.info(session_begins)
            logging.info("AAI Listening ...")

            async def send():
                # Clear the audio buffer
                # This was originally to help Daisy from speaking over itself. Delete if no problem.
                #if stream.get_read_available() > 0:
                #    print("cleaning stream")
                #    stream.read(stream.get_read_available())

                logging.info("TTS Send start")
                #When a result is received, close the loop, allowing stt_send_receive to finish (Let me diiiiieeeee)

                #Get the beep as CLOSE to the audio recorder as possible
                sounds.play_sound("beep")
                while self.result_received == False:
                    try:
                        data = stream.read(FRAMES_PER_BUFFER)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio_data":str(data)})
                        await _ws.send(json_data)
                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.error(f"Connection closed with error code {e.code}: {e.reason}")
                        break
                    except Exception as e:
                        logging.exception(f"Unexpected error: {e}")
                        break
                    await asyncio.sleep(0.01)
                logging.info("TTS Send done")
                return
            
            async def receive():
                logging.info("TTS Receive start")
                #global result_str, result_received, new_result_str
                self.result_str = ""
                self.new_result_str = ""
                self.result_received = False
                tts_fail = False
                while True:
                    while self.result_received == False:
                        try:
                            self.new_result = await _ws.recv()
                            self.new_result_str = json.loads(self.new_result)['text']
                            if len(self.new_result_str) >= len(self.result_str):
                                self.result_str = self.new_result_str
                                # Move the cursor to the beginning of the last line
                                sys.stdout.write('\033[F')
                                # Clear the line
                                sys.stdout.write('\033[2K')
                                print("You: "+self.result_str)
                            else:
                                self.result_received = True
                                logging.info("TTS Receive done")
                                return
                        except websockets.exceptions.ConnectionClosedError as e:
                            logging.error(f"Connection closed with error code {e.code}: {e.reason}")
                            tts_fail = True
                            break
                        except Exception as e:
                            logging.exception(f"Unexpected error: {e}")
                            tts_fail = True
                            break
                    if tts_fail:
                        logging.error(f"STT Receive failed")
                        break

            
            send_result, receive_result = await asyncio.gather(send(), receive())


    def stt(self):
        """Calls stt_send_receive in a new thread and returns the final transcription."""
        # Create an event object to signal the thread to stop
        stop_event = threading.Event()

        def watch_results():
            #global result_received
            #global result_str
            while not stop_event.is_set():
                if self.result_received:
                    logging.info("Result received: %s", self.result_str)
                    self.result_received = False

                    # Set the event to signal the thread to stop
                    stop_event.set()

                time.sleep(0.1)

            # Join the thread to wait for it to finish
            logging.info("Joining thread...")
            thread.join()
            logging.info("Thread stopped")

            # Enable the ability to exit the program in a keyboard blocking state
            exit_string = self.remove_non_alpha(self.result_str.lower())
            if exit_string == "exitprogram":
                logging.info("Exiting program...")
                sys.exit(0)

            return self.result_str

        # Set up AssemblyAI stt_send_receive loop
        def start_stt_send_receive():
            asyncio.run(self.stt_send_receive())

        # Create and start the stt_send_receive thread
        thread = threading.Thread(target=start_stt_send_receive)
        thread.start()

        # Start watching results in the main thread
        result_str = watch_results()
        return result_str

    def split_text_for_google_tts(self, text):
        """Splits text into smaller chunks suitable for Google TTS."""
        logging.debug(f'Splitting text: {text}')

        # Split the text into individual words
        words = text.split()

        # Initialize an empty list to hold the split strings
        split_strings = []

        # Initialize a string variable to hold the current split string
        current_string = ''

        # Loop over each word in the text
        for word in words:
            # If adding the current word to the current split string would make it too long, add the current split string to the list and start a new one
            if len(current_string + ' ' + word) > 200:
                split_strings.append(current_string.strip())
                current_string = ''

            # Add the current word to the current split string
            current_string += ' ' + word

        # Add the last split string to the list
        if current_string.strip():
            split_strings.append(current_string.strip())

        logging.debug(f'Split text into {len(split_strings)} parts')
        logging.debug(split_strings)
        return split_strings

    def remove_non_alphanumeric(self, text):
        """Removes all characters that are not alphanumeric or punctuation."""

        # Create a set of all valid characters
        valid_chars = set(string.ascii_letters + string.digits + "!()',./?+=-_#$%&*@" + ' ')

        # Use a generator expression to filter out any invalid characters
        filtered_text = ''.join(filter(lambda x: x in valid_chars, text))

        # Log the input and output text at the DEBUG level
        logging.debug(f'Removing non-alphanumeric characters from text: {text}')
        logging.debug(f'Filtered text: {filtered_text}')

        return filtered_text

    def remove_non_alpha(self, text):
        """Removes all non-alphabetic characters (including punctuation and numbers) from a string and returns the modified string in lowercase."""

        # Log a debug message with the input string
        logging.debug(f'Removing non-alpha characters from string: {text}')

        # Use regular expression to replace non-alphanumeric characters with empty string
        text = re.sub(r'[^a-zA-Z]+', '', text)

        # Log a debug message with the modified string
        logging.debug(f'Filtered text: {text}')

        # Return the modified string
        return text.lower()
    
"""
# Initialize the ChatProcessor
chat_processor = ChatProcessor()

# Call the STT method to convert speech to text
input_text = chat_processor.stt(audio_file)

# Call the process method to generate a response
response_text = chat_processor.process(input_text)

# Call the TTS method to convert the response to speech
chat_processor.tts(response_text)
"""