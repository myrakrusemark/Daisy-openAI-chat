import logging
from elevenlabslib import *
import pydub
import pydub.playback
import io
import yaml

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
	



	def main(self, text):
		user = ElevenLabsUser(self.api_key) #fill in your api key as a string
		voice = user.get_voices_by_name("Daisy")[0]  #fill in the name of the voice you want to use. ex: "Rachel"
		self.play(voice.generate_audio_bytes(text)) #fill in what you want the ai to say as a string

	def play(self, bytesData):
		sound = pydub.AudioSegment.from_file_using_temporary_files(io.BytesIO(bytesData))
		pydub.playback.play(sound)
		return
		  
