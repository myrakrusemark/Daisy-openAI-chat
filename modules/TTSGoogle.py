import logging
import requests
from io import BytesIO
import io
import threading
from pydub import AudioSegment
from daisy_llm import ChatSpeechProcessor

class TTSGoogle:
    description = "A TTS model using Google Translate's TTS service"
    module_hook = "Tts"

    def __init__(self, ml):
        self.csp = ChatSpeechProcessor()

    def main(self, text, as_thread=False): 
        if as_thread:
            t = threading.Thread(target=self.tts, args=(text,))
            t.start()
            t.join()
        else:
            self.tts(text)

    def tts(self, text):
        audio_bytes = self.create_tts_audio(text)
        if audio_bytes:
            self.play_tts(audio_bytes)

    def create_tts_audio(self, text):
        try:
            logging.debug("Creating TTS")
            text_parts = self.split_text_for_google_tts(text)
            audio_segments = []
            for text in text_parts:
                audio_segment = self.request_audio_segment(text)
                if audio_segment:
                    audio_segments.append(audio_segment)

            combined_audio = self.combine_audio_segments(audio_segments)
            if combined_audio:
                audio_bytes = self.export_audio_bytes(combined_audio)
                return audio_bytes
            else:
                return None
        except requests.exceptions.HTTPError as e:
            logging.error("Error creating Google TTS audio.")
            return None

    def request_audio_segment(self, text):
        url = "http://translate.google.com/translate_tts"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        params = {
            "q": self.csp.remove_non_alphanumeric(text),
            "ie": "UTF-8",
            "client": "tw-ob",
            "tl": "en"
        }
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return io.BytesIO(response.content)
        except requests.exceptions.RequestException as error:
            logging.error(f"RequestException: {error}")
            return None
        except requests.exceptions.HTTPError as error:
            logging.error(f"HTTPError: {error}")
            return None

    def combine_audio_segments(self, audio_segments):
        combined_audio = AudioSegment.empty()
        for audio_segment in audio_segments:
            audio_segment.seek(0)
            try:
                combined_audio += AudioSegment.from_file(audio_segment, format="mp3")
            except CouldntDecodeError as e:
                logging.error("Error decoding the audio file. It might be empty.")
            audio_segment.close()
        return combined_audio

    def export_audio_bytes(self, audio):
        with io.BytesIO() as buffer:
            audio.export(buffer, format="mp3")
            audio_bytes = buffer.getvalue()
        return audio_bytes

    def play_tts(self, bytes_data):
        sound = AudioSegment.from_file_using_temporary_files(BytesIO(bytes_data))
        pydub.playback.play(sound)
        return

    def split_text_for_google_tts(self, text):
        words = text.split()
        split_strings = []
        current_string = ''
        for word in words:
            if len(current_string + ' ' + word) > 200:
                split_strings.append(current_string.strip())
                current_string = ''
            current_string += ' ' + word
        if current_string.strip():
            split_strings.append(current_string.strip())
        logging.debug(f'Split text into {len(split_strings)} parts')
        logging.debug(split_strings)
        return split_strings
