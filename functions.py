import speech_recognition as sr
import requests
import time
import openai
import os
from dotenv import load_dotenv
import json
#import pygame #pip install pygame --pre
import re
import threading
from serpapi import GoogleSearch
import colorama
import subprocess
import threading
import platform
import constants
import sys
import play_sound
import urllib.parse
import io
import tempfile
import string
import pygame

#Initialize
load_dotenv()
openai.api_key = os.environ["API_KEY"]
r = sr.Recognizer()

if not constants.args.no_audio:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', "english-us")


def google_tts_split_text(text):
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

    return split_strings

def remove_non_alphanumeric(text):
    # Create a set of all valid characters
    valid_chars = set(string.ascii_letters + string.digits + string.punctuation + ' ')

    # Use a generator expression to filter out any invalid characters
    filtered_text = ''.join(filter(lambda x: x in valid_chars, text))

    return filtered_text

#Check if Internet is available
class CheckInternetThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.is_connected = False

    def run(self):
        try:
            # ping google.com and check if we receive any response
            if platform.system() == 'Windows':
                output = subprocess.check_output(['ping', '-n', '1', 'google.com'])
            else:
                output = subprocess.check_output(['ping', '-c', '1', 'google.com'])
            self.is_connected = True
        except subprocess.CalledProcessError:
            self.is_connected = False

def check_internet():
    thread = CheckInternetThread()
    thread.start()
    thread.join(timeout=5) # wait for the thread to complete or timeout after 5 seconds
    return thread.is_connected


def text_to_speech(text):
    if not constants.args.no_audio:
        try:
            text_parts = google_tts_split_text(text)
            file_paths = []

            #Request multiple text parts and save to multiple temp files
            for text in text_parts:
                url = "http://translate.google.com/translate_tts"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                params = {"q": remove_non_alphanumeric(text),
                            "ie": "UTF-8",
                            "client": "tw-ob",
                            "tl": "en"}

                try:
                    response = requests.get(url, params=params, headers=headers)
                    response.raise_for_status()  # Raise an exception for non-2xx response codes

                    # Read the audio data from the response object
                    audio_data = io.BytesIO(response.content)
                except requests.exceptions.RequestException as error:
                    print(error)
                    break


                # Save the contents of the BytesIO object to a temporary file
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(audio_data.getvalue())
                    file_path = tmp_file.name
                    file_paths.append(file_path)  # Add the file path to the list

            #Play each file in sequence
            for file_path in file_paths:
                play_sound.play_mpeg(file_path, 1)

        #If Google TTS somehow fails, fallback to local TTS
        except Exception as e:
            """Converts the given text to speech using pyttsx3"""
            print(e)
            engine.say(text)
            engine.runAndWait()           




def speech_to_text(r):
    text = ""
    """Converts speech to text using speech_recognition library"""

    #If no miorophone is available, use keyboard input
    if constants.args.no_mic:
        text = input()
        text = text.lower()
    else:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening

                audio = r.listen(source)
                try:
                    text = r.recognize_google(audio, language='en-US', show_all=False)
                except sr.UnknownValueError:
                    print("Audio not understood")
                except sr.RequestError as e:
                    print("Could not request results service; {0}".format(e))
                    text_to_speech("Sorry, the request didnt work. Pleasew try again.")
                
        except sr.WaitTimeoutError:
            print(f"{colorama.Fore.RED}Connection timed out. {colorama.Fore.WHITE}Are you connected to the Internet? Please try again later.")

    #Enable the ability to exit the program in a keyboard blocking state
    if not constants.args.hardware_mode:
        if text.lower() == "exit program":
            print("Exiting program...")
            sys.exit(0)

    return text


def chat():
    """Engages in conversation with the user"""
    while True:
        if check_internet():

            #Get and display recognized text
            print(f"'{constants.sleep_word}' to end")
            print("You:")
            
            user_input = speech_to_text(r)
           
            web_response_text = ""

            #Only request if words spoken
            if(user_input != ""):
                #Update context with user input
                new_message = {"role": "user", "content": user_input}
                constants.messages.append(new_message)
                

                response_text = request()
                
                if response_text != False:
                    #Find a search term in the response text (If --internet)
                    if "[search:" in response_text.lower() and constants.args.internet:
                        match = re.search(r"\[search:.*\]", response_text)
                        if match:
                            web_response = match.group()
                            start = web_response.index(":") + 1
                            end = web_response.index("]")
                            search_query = web_response[start:end]
                            print(f"Searching the web ({search_query})...")
                            text_to_speech("Searching the web.")
                            new_message = {'role': 'assistant', 'content': 'Searching the web... [search:'+search_query+']'}
                            constants.messages.append(new_message)



                            params = {
                              "engine": "google",
                              "q": search_query,
                              "api_key": os.environ["SERPAPI_KEY"]
                            }
                            search = GoogleSearch(params)
                            results = search.get_dict()
                            organic_results = results["organic_results"]

                            if len(organic_results):
                                new_prompt="Here is the information from the Internet:\n\n"
                                for organic_result in organic_results:
                                    if("snippet" in organic_result):
                                        new_prompt += organic_result["snippet"]+"\n"

                                new_message = {"role": "user", "content": new_prompt}
                                constants.messages.append(new_message)

                                #Get the web answer with no previous context.
                                web_response_text = request()
                            else:
                                web_response_text = "Sorry, either there was an error or there are no results."
                    #Update context with response
                    if(web_response_text != ""):
                        new_message = {'role': 'assistant', 'content': web_response_text}
                    else:
                        new_message = {'role': 'assistant', 'content': response_text}

                    constants.messages.append(new_message)

                    #os.system("cls" if os.name == "nt" else "clear")           
                    for message in constants.messages:
                        # Check if the message role is in the list of roles to display
                        color = colorama.Fore.BLUE if message['role'] == "assistant" else colorama.Fore.GREEN
                        print(f"{color}{message['role']}: {colorama.Fore.WHITE}{message['content']}\n\n")


                    text_to_speech(new_message["content"])

                    
                #If only sleep phrase, return
                if user_input.lower() in constants.similar_sleep_words:
                        return
        else:
            #os.system("cls" if os.name == "nt" else "clear")     
            print(f"{colorama.Fore.RED}No Internet connection. {colorama.Fore.WHITE}When a connection is available the script will automatically re-activate.")
                    
        continue

def request(context=True, new_message={}):
    """Requests response from OpenAI model"""

    try:
        if not constants.args.no_audio:
            stop_event, thread = play_sound.play_sound_with_thread('waiting.wav', 0.2)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=constants.messages if context else new_message
            )
        response_text=response["choices"][0]["message"]["content"]

        if not constants.args.no_audio:
            stop_event.set()

        return response_text
    except openai.error.InvalidRequestError as e:
        print(f"Invalid Request Error: {e}")
        if not constants.args.no_audio:
            constants.stop_sound = True
        text_to_speech("Invalid Request Error. Sorry, I can't talk right now.")
        return False        
    except openai.APIError as e:
        print(f"API Error: {e}")
        if not constants.args.no_audio:
            constants.stop_sound = True
        text_to_speech("API Error. Sorry, I can't talk right now.")
        return False
    except ValueError as e:
        print(f"Value Error: {e}")
        if not constants.args.no_audio:
            constants.stop_sound = True
        text_to_speech("Value Error. Sorry, I can't talk right now.")
        return False    
    except TypeError as e:
        print(f"Type Error: {e}")
        if not constants.args.no_audio:
            constants.stop_sound = True
        text_to_speech("Type Error. Sorry, I can't talk right now.")
        return False     

def listen_for_wake_word():
    #os.system("cls" if os.name == "nt" else "clear")           

    #If no miorophone is available, use keyboard input
    if constants.args.no_mic:
        text = input()
        text = text.lower()
    else:
        with sr.Microphone() as source:


            try:
                r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening
                print(f"Waiting for wake word: '{constants.wake_word}'")
                audio = r.listen(source)
            except sr.WaitTimeoutError:
                return False
            
            try:
                print("Recognizing...")
                text = r.recognize_google(audio)
                text = text.lower()
                print(text)
                       
            except Exception as error:
                print(error)
                return False

    if not constants.args.hardware_mode:
        if text.lower() == "exit program":
            print("Exiting program...")
            sys.exit(0)

    if text in constants.similar_wake_words:
        stop_event, thread = play_sound.play_sound_with_thread('alert.wav')

        return True

