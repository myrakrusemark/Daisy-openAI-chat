import logging
import requests
import io

import modules.ChatSpeechProcessor as csp
import modules.SoundManager as sm

class TtsGoogle:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "A TTS model using Google Translate's TTS service"
    module_hook = "Tts"

    def __init__(self):
        self.csp = csp.instance
        self.sounds = sm.instance



    def main(self, text):
        """Converts text to speech using Google TTS or a fallback TTS engine."""
        text_parts = self.split_text_for_google_tts(text)
        #file_paths = []
        audio_datas = []

        # Request multiple text parts and save to multiple temp files
        for text in text_parts:
            url = "http://translate.google.com/translate_tts"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            params = {"q": self.csp.remove_non_alphanumeric(text),
                        "ie": "UTF-8",
                        "client": "tw-ob",
                        "tl": "en"}

            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()  # Raise an exception for non-2xx response codes

                # Read the audio data from the response object
                audio_data = io.BytesIO(response.content)
                # Create a file-like object from the BytesIO object
                audio_data.seek(0)
            except requests.exceptions.RequestException as error:
                # Log the error message instead of printing it to stdout
                logging.error(f'RequestException: {error}')
                break


            # Save the contents of the BytesIO object to a temporary file
            audio_datas.append(audio_data)

        # Play each file in sequence
        for audio_data in audio_datas:
            self.sounds.play_sound(audio_data, 1)

        # If Google TTS somehow fails, fallback to local TTS
        #except Exception as e:
            # Log the error message instead of printing it to stdout
        #    logging.error(f'Exception: {e}')
        #    engine.say(text)
        #    engine.runAndWait()  

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

