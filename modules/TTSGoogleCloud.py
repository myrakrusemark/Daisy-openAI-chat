import simpleaudio as sa
from io import BytesIO
from google.cloud import texttospeech
import threading
import requests
import logging
import yaml
import os

class TTSGoogleCloud:
	description = "A TTS model using Google Cloud's TTS service"
	module_hook = "Tts"
	
	def __init__(self, ml):

		with open("configs.yaml", "r") as f:
			configs = yaml.safe_load(f)
			self.api_key = configs["keys"]["elevenlabs"]
			self.voice_config = configs["TTSGoogleCloud"]["voice"]
			self.project = configs["TTSGoogleCloud"]["project"]

			#set self.project as environment variable
			os.environ["GOOGLE_CLOUD_PROJECT"] = self.project

			self.client = texttospeech.TextToSpeechClient()

			self.voice = texttospeech.VoiceSelectionParams(
				language_code="en-US", name=self.voice_config, ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
			)
			
		self.audio_config = texttospeech.AudioConfig(
			audio_encoding=texttospeech.AudioEncoding.LINEAR16
		)


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

			synthesis_input = texttospeech.SynthesisInput(text=text)

			response = self.client.synthesize_speech(
				input=synthesis_input, voice=self.voice, audio_config=self.audio_config
			)

			return response.audio_content
		
		except requests.exceptions.HTTPError as e:
			logging.error(f"Error creating TTS audio. Check your GoogleCloud account: {e}")
			return None


	def play_tts(self, bytesData):
		# Create a sound object from the bytes data
		sound = sa.WaveObject.from_wave_file(BytesIO(bytesData))

		# Play the sound and wait for it to finish
		play_obj = sound.play()
		play_obj.wait_done()
		return

