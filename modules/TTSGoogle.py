import logging
import requests
from io import BytesIO
import io
import threading
from pydub import AudioSegment
import system_modules.ChatSpeechProcessor as csp

class TTSGoogle:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A TTS model using Google Translate's TTS service"
	module_hook = "Tts"

	def __init__(self):
		self.csp = csp.ChatSpeechProcessor()

	def main(self, text, as_thread=False): 
		if as_thread:
			t = threading.Thread(target=self.tts, args=(text,))
			t.start()
			t.join()
		else:
			self.tts(text)

	def tts(self, text):
		self.create_tts_audio(text)
		self.play_tts(self.voice.create_bytes(text)) 

	def create_tts_audio(self, text):
		try:
			logging.debug("Creating TTS")

			"""Converts text to speech using Google TTS or a fallback TTS engine."""
			text_parts = self.split_text_for_google_tts(text)

			# Request multiple text parts and save to multiple temp files		
			url = "http://translate.google.com/translate_tts"
			headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
			audio_segments = []
			for text in text_parts:
				params = {"q": self.csp.remove_non_alphanumeric(text),
							"ie": "UTF-8",
							"client": "tw-ob",
							"tl": "en"}

				try:
					response = requests.get(url, params=params, headers=headers)
					response.raise_for_status()  # Raise an exception for non-2xx response codes

				except requests.exceptions.RequestException as error:
					# Log the error message instead of printing it to stdout
					logging.error(f'RequestException: {error}')
						
				audio_segments.append(io.BytesIO(response.content))

			combined_audio = AudioSegment.empty()
			for audio_segment in audio_segments:
				audio_segment.seek(0) # Reset the buffer to the beginning
				combined_audio += AudioSegment.from_file(audio_segment, format="mp3")
				audio_segment.close()
				
			with io.BytesIO() as buffer:
				combined_audio.export(buffer, format="mp3")
				audio_bytes = buffer.getvalue()
			
			return audio_bytes

		except requests.exceptions.HTTPError as e:
			logging.error(f"Error creating Google TTS audio.")
			return None


	def play_tts(self, bytesData):
		# Create a sound object from the bytes data
		sound = AudioSegment.WaveObject.from_wave_file(BytesIO(bytesData))

		# Play the sound and wait for it to finish
		play_obj = sound.play()
		play_obj.wait_done()
		return



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

