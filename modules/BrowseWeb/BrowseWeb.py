import requests
from bs4 import BeautifulSoup

class BrowseWeb:
    description = "Converts a web page to Markdown format."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        markdown = self.convert_to_markdown(arg)
        return markdown

    def convert_to_markdown(self, input_url):
        try:
            # Use regular expression to extract the URL
            import re
            match = re.search("(?P<url>https?://[^\s]+)", input_url)
            if match is None:
                return "Error: Invalid URL."
            url = match.group("url")

            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
                
            # Find the title of the web page
            title = soup.find('title').get_text().strip()
            
            # Generate Markdown with page title
            markdown = f'# {title}\n\n'
            
            # Find all headings in the HTML content and convert them to Markdown
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().strip()
                heading_level = int(heading.name[-1])
                markdown += f'{"#" * heading_level} {heading_text}\n\n'
            
            # Find all anchor tags (links) in the HTML content and convert them to Markdown
            anchor_tags = soup.find_all('a')
            for tag in anchor_tags:
                if "href" in tag:
                    link_url = tag['href']
                    link_text = tag.get_text()
                    markdown += f'- [{link_text}]({link_url})\n'
                
            # Find all paragraphs and bulleted lists in the HTML content and convert them to Markdown
            paragraphs = soup.find_all(['p', 'ul'])
            for p in paragraphs:
                if p.name == 'p':
                    paragraph_text = p.get_text().strip()
                    markdown += f'\n{paragraph_text}\n\n'
                elif p.name == 'ul':
                    for li in p.find_all('li'):
                        li_text = li.get_text().strip()
                        markdown += f'- {li_text}\n'
            
            return markdown
            
        except Exception as e:
            print("Error:", e)
            return "Error: Unable to convert the web page to Markdown."

