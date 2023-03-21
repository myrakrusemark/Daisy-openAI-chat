#import speech_recognition as sr
import pyaudio
import websockets
import asyncio
import concurrent.futures
import base64
import json
import threading
import time
from modules import constants
import sys
import os
import re
import string
from dotenv import load_dotenv
import pyttsx3
import requests
import tempfile
import logging
import pygame
import pvporcupine

import modules.SoundManager as sm
import modules.Porcupine as porcupine
import modules.DaisyMethods as dm
import modules.RgbLed as led


class ChatSpeechProcessor:
    description = "A class that handles speech recognition and text-to-speech processing for a chatbot."
    module_hook = "ai_available"

    def __init__(self):
        # Set up AssemblyAI API key and websocket endpoint
        self.auth_key = "f7754f3d71ac422caf4cfc54bace4306"
        self.uri = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

        load_dotenv()

        # Define global variables
        self.result_str = ""
        self.new_result_str = ""
        self.result_received = False
        self.api_key = os.environ["AAI_KEY"]
        #self.r = sr.Recognizer()

        self.sounds = sm.instance
        self.porcupine = porcupine.instance
        self.dm = dm.instance
        self.engine = pyttsx3.init()
        self.engine.getProperty('voices')
        self.engine.setProperty('voice', "english-us")
        self.led = led.instance


    def listen_for_wake_word(self):
        self.porcupine.show_audio_devices()
        return self.porcupine.run()

    def tts(self, text):
        #HOOK: Tts
        try:
            import ModuleLoader as ml
            Tts_instances = ml.instance.Tts_instances
            if Tts_instances:
                for instance in Tts_instances:
                    logging.info("Running Tts module: "+type(instance).__name__)
                    response_text = instance.main(text)
            else:
                raise Exception("No TTS module found.")

        #If TTS module somehow fails, fallback to local TTS
        except Exception as e:
            logging.warning("Tts Hook: "+str(e)+" Using local engine")
            self.engine.say(text__)
            self.engine.runAndWait()



    async def stt_send_receive(self, timeout_seconds=0):
        """Sends audio data to AssemblyAI STT API and receives text transcription in real time using websockets."""

        self.result_str = ""
        self.new_result_str = ""
        self.result_received = False

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

            async def timeout():
                start_time = time.time()
                elapsed_time = 0

                while not self.result_received:
                    elapsed_time = time.time() - start_time
                    if self.dm.get_cancel_loop():
                        logging.info("Timeout()")
                        break
                    if timeout_seconds > 0: # If timeout is 0s, then dont timeout
                        if elapsed_time > timeout_seconds:
                            logging.info("Timeout reached")
                            self.dm.set_cancel_loop(True)
                            return
                    await asyncio.sleep(0.01)

                logging.info("Timeout cancelled or result received")
                return


            async def send():
                logging.info("STT Send start")

                while not self.result_received:
                    if self.dm.get_cancel_loop():
                        logging.info("Send(): Cancelled")
                        break

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
                print("SEND RESULT RECEIVED: "+str(self.result_received))

                logging.info("Send(): STT Send done")
                return
                        
            
            async def receive():
                logging.info("STT Receive start")
                


                while not self.result_received:
                    if self.dm.get_cancel_loop():
                        logging.info("Receive(): Cancelled")
                        self.result_str = False
                        self.result_received = True
                        break
                    try:
                        self.new_result = await _ws.recv()
                        self.new_result_str = json.loads(self.new_result)['text']
                        #if self.result_str:
                        if len(self.new_result_str) >= len(self.result_str):
                            self.result_str = self.new_result_str
                        

                            logging.info("You: "+str(self.result_str))
                            self.led.turn_on_color_random_brightness(0, 0, 100)  # Random brightness Blue


                        else:
                            #DONE
                            logging.info("Receive(): STT Receive done")
                            logging.info("Receive(): You said: "+str(self.result_str))
                        
                            self.result_received = True

                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.error(f"Connection closed with error code {e.code}: {e.reason}")
                        self.result_str = False
                        self.result_received = True
                    except Exception as e:
                        logging.exception(f"Unexpected error: {e}")
                        self.result_str = False
                        self.result_received = True

                return



            
            self.sounds.play_sound_with_thread('alert')
            send_result, receive_result, timeout_result = await asyncio.gather(
                asyncio.shield(timeout()), asyncio.shield(send()), asyncio.shield(receive())
            )


    def stt(self, timeout_seconds=0):
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
            if self.result_str:
                self.result_str = self.result_str.lower()
            exit_string = self.remove_non_alpha(self.result_str)
            if exit_string == "exitprogram":
                logging.info("Exiting program...")
                sys.exit(0)

            return self.result_str


        # Set up AssemblyAI stt_send_receive loop
        #This is a thread in a thread. I think it can be reduced.
        def start_stt_send_receive():
            asyncio.run(self.stt_send_receive(timeout_seconds))

        # Create and start the stt_send_receive thread
        thread = threading.Thread(target=start_stt_send_receive)
        thread.start()

        # Start watching results in the main thread
        result_str = watch_results()

        return result_str

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
        if text:
            # Log a debug message with the input string
            logging.debug(f'Removing non-alpha characters from string: {text}')

            # Use regular expression to replace non-alphanumeric characters with empty string
            text = re.sub(r'[^a-zA-Z]+', '', text)

            # Log a debug message with the modified string
            logging.debug(f'Filtered text: {text}')

            # Return the modified string
            return text.lower()
        else:
            return False

instance = ChatSpeechProcessor()
    
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