import logging
from daisy_llm import ChatSpeechProcessor, LoadTts

class TTS:
	description = "A module for speaking aloud."
	module_hook = "Chat_request_inner"
	tool_form_name = "Speak"
	tool_form_description = """Speaks aloud any text provided."""
	tool_form_argument = "Text to speak aloud."

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.csp = ChatSpeechProcessor()

		self.tts = None
		t = LoadTts(self, self.ml)
		t.start()
		#t.join()

	def main(self, text, stop_event):
		logging.info("TTS: Speaking: " + text)
		self.csp.tts(text, self.tts)
		return "TTS Tool: Spoke aloud: " + text

	def calculate_expression(self, expression):
		try:
			result = eval(expression)
			return str(result)
		except Exception as e:
			logging.error("TTS: Error: " + str(e))
			return "Error: Unable to speak."

