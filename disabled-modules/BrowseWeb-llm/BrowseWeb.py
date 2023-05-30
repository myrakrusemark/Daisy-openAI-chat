import logging
import requests
from bs4 import BeautifulSoup
import sys
import openai
import re  # import regular expression module
import sys
from tqdm import tqdm
from threading import Thread
import itertools
import time
import dirtyjson
import daisy_llm.Chat as chat

import concurrent.futures
import sys
import dirtyjson
import logging
from typing import List, Dict

import shutil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Chrome options for running in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")


class BrowseWeb:
	description = "Converts a web page to text."
	module_hook = "Chat_request_inner"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch
	
		self.chat = None
		self.max_results = 5
		self.max_length = 1000 
		self.overlap = 0.0

		#GPT-3.5-turbo Settings
		self.model = "gpt-3.5-turbo"
		self.prompt_cost_per_k = 0.002
		self.completion_cost_per_k = 0.002
		self.token_avg_char_length = 4.0
		self.max_tokens_per_min = 90000

		self.max_length_tokens = self.max_length / self.token_avg_char_length


	def get_prompt(self, search_term: str) -> str:
		prompt = "\n\n"
		prompt += "-----------------------------------------"
		prompt += "\n\n"
		prompt += "Respond \"No\" if the content in the last message is not related to the search term.\n"
		prompt += "Otherwise, respond with a number 1-100 for how effectively it answers the search term.\n"
		prompt += f"Search term: {search_term}\n"
		return prompt
	
	def get_section_result(self, section: str, search_term: str) -> Dict[str, str]:

		try:
			response = self.chat.request(
				messages=[{'role': 'user', 'content': section+self.get_prompt(search_term)}],
				model=self.model,
				silent=True,
				response_label=False,
				temperature=0.0,
				max_tokens=3
			)
			print(response)

			if response == False:
				return None


			confidence = re.findall(r'\d+', response)
			if confidence:
				confidence = int(re.findall(r'\d+', response)[0]) #Get confidence percentage
				if confidence:
					result = {'section': section, 'confidence': confidence}
					return result
				else:
					return False
			else:
				return False
		except Exception as e:
			logging.error("BrowseWeb request error: "+ str(e))
			return None


	def main(self, arg, stop_event):
		# corrected calculations
		tokens_per_second = self.max_tokens_per_min / 60
		requests_per_second = tokens_per_second / self.max_length_tokens
		request_rest_time = 1 / requests_per_second if requests_per_second != 0 else 0
		requests_per_minute = requests_per_second * 60

		# corrected calculation
		tokens_per_minute = requests_per_minute * self.max_length_tokens


		print("Requests per minute: ", requests_per_minute)
		print("Requests rest time (in seconds): ", request_rest_time)
		print(f"Tokens per minute: {tokens_per_minute}")

		
		self.chat = chat.Chat(self.ml, self.ch)

		arg_data = dirtyjson.loads(arg)
		url = arg_data["url"]

		if not url.startswith("https://"):
			url = "https://" + url
		search_term = arg_data["request"]

		# Retrieve webpage content and strip HTML tags
		animation = LoadingAnimation()
		animation.start()
		webpage_content = self.get_webpage_content(url, animation)

		if len(webpage_content) <= self.max_length:
			return webpage_content
		
		sections, full_text_length = self.split_content_into_sections(webpage_content, search_term)
		num_sections = len(sections)
		total_tokens = full_text_length/self.token_avg_char_length

		estimated_cost = total_tokens/1000 * self.prompt_cost_per_k

		print("Sections: ", num_sections)
		print("Tokens: ", total_tokens)
		print(f"Estimated Cost: >${estimated_cost} USD")

		#cont = input("Continue? (y/n): ")
		#if cont.lower() != "y":
		#	return "Cancelled."

		# Map the number of sections to the number of columns in the terminal
		num_columns = self.get_terminal_size()[0]

		# Calculate the width of each block
		block_width = max(num_columns // num_sections, 1)

		# Initialize the terminal status line with black blocks
		status_line = ['\033[40m' + ' ' * block_width + '\033[0m'] * num_sections

		results = []
		section_queue = sections.copy()  # Queue of sections to process
		section_to_future = {}  # Map from section text to Future
		count = 0
		start_time = time.time()

		with concurrent.futures.ThreadPoolExecutor() as executor:
			# Initially submit all sections
			for section in section_queue:
				future = executor.submit(self.get_section_result, section, search_term)
				section_to_future[section] = future

			while section_queue:
				# Wait for the next future to complete
				done, _ = concurrent.futures.wait(section_to_future.values(), return_when=concurrent.futures.FIRST_COMPLETED)
				for future in done:
					section = [s for s, f in section_to_future.items() if f == future][0]
					section_queue.remove(section)
					del section_to_future[section]

					# Update status line with a white block for a non-match, red block for a failure, and a green block for a match
					index = sections.index(section)
					if future.result() is None:
						status_line[index] = '\033[41m' + ' ' * block_width + '\033[0m'  # red block
						section_queue.append(section)  # Retry failed section
						future_retry = executor.submit(self.get_section_result, section, search_term)
						section_to_future[section] = future_retry
					elif future.result():
						status_line[index] = '\033[42m' + ' ' * block_width + '\033[0m'  # green block
						results.append(future.result())
					else:
						status_line[index] = '\033[47m' + ' ' * block_width + '\033[0m'  # white block

					print(''.join(status_line), end='\r')  # print updated status line and return to the beginning of the line
					count += 1

					time.sleep(2)


		results.sort(key=lambda x: x['confidence'], reverse=True)
		results = results[:self.max_results]

		if len(results) == 0:
			return "No relevant information found on this page."

		output = ""
		for result in results:
			output += result["section"]
			output += "\n\n"

		output += str(len(results))+" relevant page sections above.\n\n"

		return output



	def get_webpage_content(self, url, animation):
		# Set up the Chrome driver
		driver = webdriver.Chrome(options=chrome_options)

		try:
			# Load the webpage
			driver.get(url)

			# Wait for the page to fully load
			WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.TAG_NAME, "body"))
			)

			# Get the page source
			page_source = driver.page_source

			# Stop the loading animation
			animation.stop()

			# Parse the page source with BeautifulSoup
			soup = BeautifulSoup(page_source, "html.parser")

			# Find all 'a' tags and modify their text
			for a in soup.find_all('a', href=True):
				if a.text:
					a.string = f"{a.text}[{a['href']}]"

			return str(soup)

		finally:
			# Quit the driver to close the browser
			driver.quit()
	
	def split_content_into_sections(self, content, search_term):


		prompt_length = len(self.get_prompt(search_term))

		# Parse the content with Beautiful Soup
		soup = BeautifulSoup(content, "html.parser")

		# Extract plain text content
		full_text = soup.get_text(separator="\n")

		# Remove consecutive newline characters
		full_text = re.sub('\n+', '\n', full_text)

		length = self.max_length - prompt_length

		# Split full_text into sections
		sections = []
		start = 0
		end = length

		while start < len(full_text):
			sections.append(full_text[int(start):int(end)])
			start = end# - (self.max_length * self.overlap)
			end = start + length

		# Add a prompt to each section (for cost estimation)
		full_length = len(full_text) + prompt_length*len(sections)

		return sections, full_length
	
	def num_tokens_from_string(self, string: str, token_avg_char_length: int) -> int:
		"""Returns the number of tokens in a text string."""
		num_tokens = len(string) / token_avg_char_length
		return num_tokens
	
	def get_terminal_size(self):
		return shutil.get_terminal_size()

	
class LoadingAnimation:
	def __init__(self):
		self.stop_loading = False

	def start(self):
		self.animation = Thread(target=self.animate)
		self.animation.start()

	def animate(self):
		for c in itertools.cycle(['.  ', '.. ', '...', '   ']):
			if self.stop_loading:
				break
			sys.stdout.write('\rLoading URL' + c)
			sys.stdout.flush()
			time.sleep(0.5)
		sys.stdout.write('\rDone!        ')

	def stop(self):
		self.stop_loading = True
		self.animation.join()
