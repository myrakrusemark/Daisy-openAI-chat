import logging
import re
import json
import threading
from daisy_llm import ChatSpeechProcessor, ConnectionStatus, SoundManager, Chat, LoadTts
from daisy_llm.Text import print_text
from modules.Daisy.DaisyMethods import listen_for_daisy_wake, listen_for_daisy_cancel
import modules.RgbLed as led

class Daisy:
	description = "Provides a user flow for Chat"
	module_hook = "Main_start"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.chat = Chat(self.ml, self.ch)
		self.csp = ChatSpeechProcessor()
		self.cs = ConnectionStatus()
		self.sounds = SoundManager()
		self.led = led.RgbLed()
		self.tts = None

		self.threads = []
		self.daisy_stop_event = threading.Event()
		self.awake_stop_event = threading.Event()
		self.dc_t = threading.Event()

		self.internet_warning_logged = False

		self.rt_event_q = self.ml.messaging_system.subscribe("rt_event")


	def main(self):
		#self.sounds.play_sound("beep", 0.5)
		print_text("🌼 DAISY - Voice Assistant 🌼", "pink", "\n")

		#self.chat = Chat(ml, ch)
		self.initialize_tts()
		self.check_internet()

		self.awake_stop_event.clear()

		self.ch.new_conversation()

		next_goal = None

		self.rt_event_q = self.ml.messaging_system.subscribe("rt_event")
		while True:

			#self.wait_for_wake_word()

			self.daisy_wake()

			#Publish inputs
			if not next_goal:
				#stt_text = self.csp.stt(self.awake_stop_event, 30, 'alert') #30s timeout
				stt_text = input("User: ")
				self.ml.messaging_system.publish("rt_event", "Speech to text input from the user: "+stt_text)
			else:
				self.ml.messaging_system.publish("rt_event", next_goal)
			#self.ml.messaging_system.unsubscribe("rt_event", self.rt_event_q)


			sound_stop_event = threading.Event()
			#self.sounds.play_sound_with_thread('waiting', 0.2, self.awake_stop_event, sound_stop_event)

			prompt = self.build_prompt()
			logging.info(prompt)

			prompt_obj = self.ch.single_message_context("system", prompt, incl_timestamp=False)
			messages = self.ch.get_context_without_timestamp()
			messages.append(prompt_obj)

			#Generate Plan
			response_data = None
			while not response_data:
				response = None
				try:
					response = self.chat.request(
						messages=messages,
						stop_event=self.awake_stop_event,
						sound_stop_event=sound_stop_event,
						tool_check=False,
						model="gpt-4",
						tts=None
						)
				except Exception as e:
					logging.error("Daisy request error: "+ e)
					self.awake_stop_event.set()
					break

				if response:
					response_data = self.parse_json_from_response(response)

					if not response_data:
						continue

					#Get next goal
					next_goal = response_data[0]['thoughts']['next_goal']

					#Run commands
					commands = None
					if response_data[0]['command']:
						commands = response_data[0]['command']

					if commands:
						output = self.chat.find_and_run_tools(commands, self.daisy_stop_event)

						#Publish inputs
						#self.rt_event_q = self.ml.messaging_system.subscribe("rt_event")
						self.ml.messaging_system.publish("rt_event", output)

				else:
					logging.error("Daisy request error: No response")
					self.awake_stop_event.set()
					break

		self.handle_sleep()
		self.ml.messaging_system.unsubscribe("rt_event", self.rt_event_q)


	def parse_json_from_response(self, response):
		#Parse JSON response
		data = None
		if response:
			start_index = response.find('[')
			if start_index >= 0:
				end_index = response.rfind(']') + 1
				json_data = response[start_index:end_index]
				try:

					# Attempt to load the input string as JSON
					try:
						data = json.loads(json_data)
						logging.info('Data:' + str(data))
					except json.decoder.JSONDecodeError as e:
						# Input string contains errors, attempt to fix them
						logging.error('JSONDecodeError:', e)
						
						# Search for keys with missing values
						match = json_data.search(json_data)
						if match:
							# Replace missing values with empty strings
							fixed_str = json_data[:match.end()] + '""' + json_data[match.end()+1:]
							logging.warning('Fixed input:', str(fixed_str))
							try:
								data = json.loads(fixed_str)
								logging.info('Data:'+ str(data))
							except json.decoder.JSONDecodeError:
								logging.error('Could not fix input')
						else:
							logging.error('Could not fix input')

				except json.decoder.JSONDecodeError as e:
					logging.error("JSONDecodeError: "+str(e))
			else:
				logging.warning("No JSON data found in string.")

			logging.info("Tool form chosen: "+str(data))
		return data

	def close(self):
		self.daisy_stop_event.set()

	def initialize_tts(self):
		self.chat = Chat(self.ml, self.ch)
		t = LoadTts(self, self.ml)
		t.start()
		t.join()

	def check_internet(self):
		self.awake_stop_event.clear()
		t = threading.Thread(target=self.cs.check_internet, args=(self.daisy_stop_event, self.awake_stop_event))
		self.threads.append(t)
		t.start()
		

	def wait_for_wake_word(self):
		self.led.turn_on_color(0, 100, 0)  # Solid Green
		awake = listen_for_daisy_wake(self.daisy_stop_event, self.awake_stop_event)
		self.led.breathe_color(100, 100, 100)  # Breathe Blue
		return awake

	def daisy_wake(self):
		#self.dc_t = threading.Thread(target=listen_for_daisy_cancel, args=(self.daisy_stop_event, self.awake_stop_event))
		#self.threads.append(self.dc_t)
		#self.dc_t.start()
		try:
			from daisy_llm import ModuleLoader as ml
			hook_instances = self.ml.hook_instances
			if "Daisy_wake" in hook_instances:
				Daisy_wake_instances = hook_instances["Daisy_wake"]
				for instance in Daisy_wake_instances:
					logging.info("Running Daisy_start module: " + type(instance).__name__)
					response_text = instance.main()
		except Exception as e:
			logging.warning("Daisy_wake Hook: " + str(e))


	def handle_sleep(self):
		#self.dc_t.join()
		self.sounds.play_sound_with_thread('end', 1.0)
		thread = threading.Thread(target=self.ch.update_conversation_name_summary, args=())
		thread.start()

	def handle_user_input(self):
		self.led.breathe_color(0, 0, 100)  # Breathe Blue
		stt_text = self.csp.stt(self.awake_stop_event, 30, 'alert')  # 30s timeout
		if self.awake_stop_event.is_set():
			return None
		if stt_text and not self.awake_stop_event.is_set():
			self.led.breathe_color(100, 0, 100)  # Breathe Blue #NEEDS CANCEL LOOP
			self.ch.add_message_object('user', stt_text)
			if self.awake_stop_event.is_set():
				return None
			sound_stop_event = threading.Event()
			self.sounds.play_sound_with_thread('waiting', 0.2, self.awake_stop_event, sound_stop_event)

			try:
				text = self.chat.request(
					messages=self.ch.get_context_without_timestamp(),
					stop_event=self.awake_stop_event,
					sound_stop_event=sound_stop_event,
					tool_check=False,
					tts=self.tts
				)
			except Exception as e:
				logging.error("Daisy request error: " + str(e))
				self.awake_stop_event.set()
				return None

			if not text:
				logging.error("Daisy request error: No response")
				self.awake_stop_event.set()
				return None

			self.ch.add_message_object('assistant', text)

			if self.awake_stop_event.is_set():
				return None

			self.led.breathe_color(100, 100, 100)  # Breathe White

			return text

	def build_prompt(self):
		prompt = "You are Daisy, a helpful AI assistant.\n"
		prompt += "Your decisions must always be made independently without seeking user assistance. Play to your strengths as an LLM and pursue simple strategies with no legal complications.\n"
		prompt += "\n"
		prompt += "INPUT:\n"
		
		for rt_event_message in self.ml.messaging_system.listen(self.rt_event_q, False):
			try:
				prompt += rt_event_message['data']+"\n"
				logging.info("Received message: "+rt_event_message['data'])
			except self.ml.messaging_system.UnsubscribeException as e:
				logging.info("Unsubscribed from channel:")

		prompt += "\n"

		prompt += "Commands:\n"
		i=1
		for module in self.ml.get_available_modules():

			if 'tool_form_name' in module:
				prompt += f"{i}. "
				prompt += f"Name: {module['tool_form_name']}\n"
				i+=1
				if 'tool_form_description' in module:
					prompt += f"Description: {module['tool_form_description']}\n"
				if 'tool_form_argument' in module:
					prompt += f"Input: <{module['tool_form_argument']}>\n"
				prompt += "\n"
		i+=1
		prompt += str(i)+". Name: Task Complete\n"
		prompt += str(i)+". Description: To be run whenever the task is complete\n"
		prompt += str(i)+". Input: <Summary of work done>\n"
		prompt += "\n"
		prompt += "Performance Evaluation:\n"
		prompt += "1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities.\n"
		prompt += "2. Constructively self-criticize your big-picture behavior constantly.\n"
		prompt += "3. Reflect on past decisions and strategies to refine your approach.\n"
		prompt += "4. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.\n"
		prompt += "\n"
		prompt += "You should only respond in JSON format as described below \n"
		prompt += "Response Format: \n"
		prompt += "[{\n"
		prompt += '	"command": [\n'
		prompt += '		{"command": "name", "arg": "input"}\n'
		prompt += '	],\n'
		prompt += '	"thoughts": {\n'
		prompt += '		"text": "thought",\n'
		prompt += '		"reasoning": "reasoning",\n'
		prompt += '		"plan": "- short comma separated list that conveys long-term plan. consider available commands.",\n'
		prompt += '		"criticism": "constructive self-criticism",\n'
		prompt += '		"request_done": "Will the task be complete with the sending of this message? Respond with \"Y\" or \"N\"",\n'
		prompt += '		"next_goal": "goal for the next iteration. consider available commands"\n'
		prompt += '	}\n'
		prompt += '}]\n'
		prompt += "\n"
		prompt += "Ensure the response can be parsed by Python json.loads"

		return prompt
		