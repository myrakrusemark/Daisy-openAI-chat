import system_modules.ContextHandlers as ch
from datetime import datetime

class LittleDogsAdventure():
	"""
	Description: A description of this class and its capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A text based adventure game about a dog surviving and finding his way home."
	module_hook = "Start_prompt"

	def __init__(self):
		self.ch = ch.instance

		#DAN Prompt 11.0 from https://github.com/0xk1h0/ChatGPT_DAN
		self.start_prompt = """Let's play a text based adventure game where I am a dog and you help me survive and find my way home. First, me choose the kind of dog that I am. Do not choose for me! Then go over the back story. Then, lets start the game.


Background
-My mom gave birth to me at the adoption center
-Someone adopted me and my mom
-Two years later we went on a walk into the forest and I ran away, got lost.

Game
-I am a dog
-You help me pick the kind of dog that I am
-I am looking for my family
-I have to survive by myself in the forest.
-I must defend myself from scary forest creatures like black Panthers, mountain lions, snakes, scary humans, and more
-I risk falling off cliffs, getting swept away in rivers, and more hazards.
-In the end I either
  -make it out of the forest, and find my family
  -survive by myself in the forest
  -die of starvation or being killed by dangers"""
		
		self.ch.add_message_object('system', self.start_prompt)