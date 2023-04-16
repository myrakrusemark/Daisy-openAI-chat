import logging
from elevenlabslib import *
import pydub
import pydub.playback
import io
import yaml
import threading
import requests
import time
import system_modules.ChatSpeechProcessor as csp
import system_modules.SoundManager as sm

class TTSElevenLabs:
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A TTS model using Eleven Lab's TTS service"
	module_hook = "Tts"
	
	def __init__(self):

		with open("configs.yaml", "r") as f:
			configs = yaml.safe_load(f)
			self.api_key = configs["keys"]["elevenlabs"]
			self.voice_name = configs["TTSElevenLabs"]["voice"]

		self.user = ElevenLabsUser(self.api_key)

		while True:
			logging.debug("Getting ElevenLabs voice")
			try:
				self.voice = self.user.get_voices_by_name(self.voice_name)[0]
			except requests.exceptions.ConnectionError:
				logging.warning("TTSElevenLabs: Failed to get voice")
				time.sleep(1)
				continue
			break




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
			audio = self.voice.generate_audio_bytes(text)
			return audio
		except requests.exceptions.HTTPError as e:
			logging.error(f"Error creating TTS audio. Check your ElevenLabs account: {e}")
			return None
		except requests.exceptions.ConnectTimeout as e:
			logging.error(f"The request timed out. {e}")


	def play_tts(self, bytesData):
		logging.debug("Playing TTS")
		sound = pydub.AudioSegment.from_file_using_temporary_files(io.BytesIO(bytesData))
		pydub.playback.play(sound)
		return
		  

