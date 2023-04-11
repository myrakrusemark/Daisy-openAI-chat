import logging
from elevenlabslib import *
import pydub
import pydub.playback
import io
import yaml
import threading

import modules.ChatSpeechProcessor as csp
import modules.SoundManager as sm

class TtsElevenLabs:
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

		self.user = ElevenLabsUser(self.api_key)
		self.voice = self.user.get_voices_by_name("Daisy")[0]




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
		logging.debug("Creating TTS")
		return self.voice.generate_audio_bytes(text)

	def play_tts(self, bytesData):
		logging.debug("Playing TTS")
		sound = pydub.AudioSegment.from_file_using_temporary_files(io.BytesIO(bytesData))
		pydub.playback.play(sound)
		return
		  

