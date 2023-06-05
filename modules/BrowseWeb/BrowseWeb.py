import logging
from bs4 import BeautifulSoup
import sys
from threading import Thread
import itertools
import time
import dirtyjson
import concurrent.futures
import shutil
import torch
from transformers import pipeline
import re
import math
import itertools

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
	
		self.avg_token_length = 3
		self.max_tokens_returned = 5000
		self.max_output_length = self.max_tokens_returned * self.avg_token_length
		self.search_results_per_url = 2

		self.batch_size = 1

		# Create a pipeline for feature extraction
		self.feature_extraction = pipeline('feature-extraction', model='bert-base-uncased', tokenizer='bert-base-uncased')
		self.max_passage_token_length = 500

	def main(self, arg, stop_event):
		arg_data = dirtyjson.loads(arg)
		urls = arg_data["urls"]

		combined_output = ""
		for url in urls:
			output = ""

			if not url.startswith("https://"):
				url = "https://" + url
				
			if "request" in arg_data:
				search_term = arg_data["request"]
			else:
				search_term = ""

			# Generate embedding for search term
			search_term_embedding = self.generate_embedding([search_term])[0]
			if isinstance(search_term_embedding, list):  
				search_term_embedding = torch.Tensor(search_term_embedding)

			# Retrieve webpage content and strip HTML tags
			animation = LoadingAnimation()
			animation.start(url)
			passages, full_text = self.get_webpage_content(url, animation)
			if not passages:
				output += "------------------------------------------------------\n"
				output += "Error: Unable to retrieve webpage content for "+url+"\n"
				output += "------------------------------------------------------\n\n"
				combined_output += output
				continue

			
			#If the page is small, then just return the full text
			if len(full_text) <= self.max_output_length:
				output += "------------------------------------------------------\n"
				output += "Full text for "+url+"\n"
				output += "------------------------------------------------------\n\n"
				output += full_text+"\n\n"

				combined_output += output
				continue
		
			# Compare each passage to the search term and order by relevance
			num_passages = len(passages)
			results = []
			print("Searching " + str(num_passages) + " passages for relevant information...")
			with concurrent.futures.ThreadPoolExecutor() as executor:
				# Batch the passages
				passage_to_future = {}  # Map from batch of passages to Future
				for i in range(0, len(passages), self.batch_size):
					batch = passages[i:i + self.batch_size]
					future = executor.submit(self.get_passage_result, batch, search_term_embedding)
					passage_to_future[tuple(batch)] = future
				passages_to_future = len(passage_to_future)
				while passage_to_future:
					# Wait for the next future to complete
					#print number of threads
					done, _ = concurrent.futures.wait(passage_to_future.values(), return_when=concurrent.futures.FIRST_COMPLETED)
					for future in done:
						batch = [s for s, f in passage_to_future.items() if f == future][0]
						del passage_to_future[batch]

						for passage in batch:
							index = passages.index(passage)

							results_from_future = future.result()

							for result in results_from_future:
								index = result['index']  # get the original index from the result
								score = result['confidence']
								passage = result['passage']
								
								#Append the last half of the passage preceding and the first half of the next passage
								if index > 0:
									passage_before = passages[index-1][1]
									last_half_before = passage_before[len(passage_before)//2:]
									result['passage'] = last_half_before + result['passage']

								if index < len(passages) - 1:
									passage_after = passages[index+1][1]
									first_half_after = passage_after[:len(passage_after)//2]
									result['passage'] += first_half_after

								results.append(result)

								progress = 100 - (len(passage_to_future) / passages_to_future) * 100
								progress_message = "Progress: {:.2f}% ({} of {})".format(progress, passages_to_future - len(passage_to_future), passages_to_future)
								print('\r' + ' '*100, end='\r')
								print("Score: {:.2f}".format(score)+" | Matches: " + str(len(results)) + " | " + progress_message)
			
			#Sort results by confidence
			results.sort(key=lambda x: x['confidence'], reverse=True)			

			#Generate output
			output += "------------------------------------------------------\n"
			output += "Relevant passages for "+url+"\n"
			output += "------------------------------------------------------\n\n"

			for result in results[:self.search_results_per_url]:
				output += result["passage"] + "\n\n"

			combined_output += output

		#Return truncated, ordered, results
		return combined_output

	def get_passage_result(self, passages: list, search_term_embedding: torch.Tensor):
		passage_embeddings = self.generate_embedding([p[1] for p in passages])
		results = []

		for (index, passage), passage_embedding in zip(passages, passage_embeddings):
			score = torch.cosine_similarity(search_term_embedding, passage_embedding, dim=-1)			
			score = score.mean().item()
			results.append({'passage': passage, 'confidence': score, 'index': index})

		return results
	
	def generate_embedding(self, texts):
		embeddings = []
		for text in texts:
				passage = text[1] if isinstance(text, tuple) else text
				all_embeddings = torch.tensor(self.feature_extraction(passage))
				embeddings.append(all_embeddings[0][0])

		return torch.stack(embeddings)

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

			# Load page source into BeautifulSoup
			soup = BeautifulSoup(page_source, 'html.parser')

			# Get full text
			full_text = soup.get_text()

			# Remove duplicate newline characters
			full_text = re.sub('\n+', '\n', full_text)

			passage_length = self.max_passage_token_length * self.avg_token_length

			# Split tokens into sections of max_passage_word_length each
			sections = []
			for i in range(0, len(full_text), passage_length):
				passage_text = full_text[i:i+passage_length]
				sections.append((int(i/passage_length), passage_text))


			# Close the WebDriver
			driver.quit()

			return sections, full_text
		except Exception as e:
			return False, False
		finally:
			# Stop the loading animation
			animation.stop()

	
class LoadingAnimation:
	def __init__(self):
		self.stop_loading = False

	def start(self, text):
		self.animation = Thread(target=self.animate, args=(text,))
		self.animation.start()

	def animate(self, text):
		for c in itertools.cycle(['.  ', '.. ', '...', '   ']):
			if self.stop_loading:
				break
			sys.stdout.write('\rLoading '+ text + c)
			sys.stdout.flush()
			time.sleep(0.5)
		sys.stdout.write('\rDone!        ')

	def stop(self):
		self.stop_loading = True
		self.animation.join()
