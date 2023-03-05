import speech_recognition as sr
import requests
import pyttsx3
import time
import openai
import os
from dotenv import load_dotenv
import json
#import pygame #pip install pygame --pre
import play_sound
import re
import threading
from serpapi import GoogleSearch
import colorama
import subprocess
import threading
import platform
import constants
import sys


#Initialize
load_dotenv()
openai.api_key = os.environ["API_KEY"]
#pygame.init()
r = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

# Load sounds
#cwd = os.getcwd()
#waiting_sound = pygame.mixer.Sound(os.path.join(cwd, "waiting.wav"))
#waiting_sound.set_volume(0.1) # set volume to 50%
#notification_sound = pygame.mixer.Sound(os.path.join(cwd, "alert.wav"))

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
    """Converts the given text to speech using pyttsx3"""
    engine.say(text)
    engine.runAndWait()

def speech_to_text(r):
    """Converts speech to text using speech_recognition library"""
    #If no miorophone is available, use keyboard input
    if constants.args.no_mic:
        text = input().lower()
    else:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening

                audio = r.listen(source)
                try:
                    text = r.recognize_google(audio, language='en-US', show_all=False)
                except sr.UnknownValueError:
                    print("Audio not understood")
                    return ""
                except sr.RequestError as e:
                    print("Could not request results service; {0}".format(e))
                    #text_to_speech("Sorry, the request didnt work. Pleasew try again.")
                    return ""
                
        except sr.WaitTimeoutError:
            print(f"{colorama.Fore.RED}Connection timed out. {colorama.Fore.WHITE}Are you connected to the Internet? Please try again later.")
            return ""
            
    if text.lower() == "exit program":
        print("Exiting program...")
        sys.exit(0)
    else:
        return text


def chat():
    """Engages in conversation with the user"""
    while True:
        if check_internet():

            #Get and display recognized text
            print(f"'{constants.sleep_word}' to end")
            print("You:")
            
            user_input = speech_to_text(r)
            print(user_input)
           
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

                    os.system("cls" if os.name == "nt" else "clear")           
                    for message in constants.messages:
                        # Check if the message role is in the list of roles to display
                        color = colorama.Fore.BLUE if message['role'] == "assistant" else colorama.Fore.GREEN
                        print(f"{color}{message['role']}: {colorama.Fore.WHITE}{message['content']}\n\n")


                    text_to_speech(new_message["content"])

                    
                #If only sleep phrase, return
                if user_input.lower() == constants.sleep_word:
                        return
        else:
            os.system("cls" if os.name == "nt" else "clear")     
            print(f"{colorama.Fore.RED}No Internet connection. {colorama.Fore.WHITE}When a connection is available the script will automatically re-activate.")
                    
        continue

def request(context=True, new_message={}):
    """Requests response from OpenAI model"""

    try:
        #waiting_sound.play()
        stop_event, thread = play_sound.play_sound_with_stop('waiting.wav', 0.2)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=constants.messages if context else new_message
            )
        response_text=response["choices"][0]["message"]["content"]
        
        stop_event.set()
        return response_text
    except openai.error.InvalidRequestError as e:
        print(f"Invalid Request Error: {e}")
        stop_event.set()
        text_to_speech("Invalid Request Error. Sorry, I can't talk right now.")
        return False        
    except openai.APIError as e:
        print(f"API Error: {e}")
        stop_event.set()
        text_to_speech("API Error. Sorry, I can't talk right now.")
        return False
    except ValueError as e:
        print(f"Value Error: {e}")
        stop_event.set()
        text_to_speech("Value Error. Sorry, I can't talk right now.")
        return False    
    except TypeError as e:
        print(f"Type Error: {e}")
        stop_event.set()
        text_to_speech("Type Error. Sorry, I can't talk right now.")
        return False     

def listen_for_wake_word():
    os.system("cls" if os.name == "nt" else "clear")           

    print(f"Waiting for wake word: '{constants.wake_word}'")

    #If no miorophone is available, use keyboard input
    if constants.args.no_mic:
        text = input().lower()
    else:
        with sr.Microphone() as source:


            try:
                r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening
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

    if text.lower() == "exit program":
        print("Exiting program...")
        sys.exit(0)
    elif text in constants.similar_wake_words:
        return True

