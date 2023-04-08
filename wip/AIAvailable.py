import logging

from modules.ContextHandlers import ContextHandlers
start_prompt_Daisy = "You are Daisy, a voice assistant based on chatGPT, a large language model trained by OpenAI. You speak in confident but concise responses, about two sentences long. You are having a real-world vocal conversation. Current date: " + datetime.now().strftime("%Y-%m-%d")

#Build start prompt     
messages=[{"role": "user", "timestamp":"", "content": start_prompt_Daisy}]

class AIAvailable:
    """
    Description: A description of this class and its capabilities.
    Module Hook: The hook in the program where method main() will be passed into.
    """
    description = "Provides a means for the AI to run its own methods that may be used elsewhere in the program."
    module_hook = "Chat_chat_inner"

    def __init__(self):

        self.ch = ContextHandlers(messages)
        self.csp = ChatSpeechProcessor.instance

        self.start_prompt_AIAvailable = """As a chatbot running in a python environment, you now have access to various methods that are typically used elsewhere in the program! You can run any available method using this "tool form". If I ask you any question that might be best answered using one of the available methods or capabilies, always respond using a "tool form" in the following format:

                {"ai_available":{"tts":{"voice":"male", "text":"Hello World!"}}}

For example:

    User: Please speak the following outloud: "I'm a little lad who loves berries and cream!"

    Daisy: {"ai_available":{"tts":{"voice":"male", "text":"I'm a little lad who loves berries and cream!"}}}


    User: Play an alert sound

    Daisy: {"ai_available":{"play_sound":{"sound":"alert"}}}

    """

        logging.info("Adding 'AIAvailable' start prompt to context")
        self.ch.add_message_object('user', self.start_prompt_AIAvailable)

    def main(self, response_text, request):
        """Main method that takes in response_text and performs the web search, returning the search results."""
        #Find a search term in the response text (If --internet)
        web_response_text = ""
        logging.info("AIAvailable: Checking for tool forms")
        answer = ""

        # Find the start and end positions of the JSON object
        start = response_text.find("{")
        end = response_text.find("}", start) + 1

        # Extract the JSON object
        json_str = response_text[start:end]

        # Parse the JSON object into a Python dictionary
        json_obj = json.loads(json_str)

        # Print the extracted JSON object
        print(json_obj)

        if "[calculator:" in response_text.lower():
            match = re.search(r"\[calculator:.*\]", response_text)
            if match:
                processed_string = match.group()
                start = processed_string.index(":") + 1
                end = processed_string.index("]")
                expression = processed_string[start:end]
                self.csp.tts("Calculating.")
                self.ch.add_message_object('assistant', 'Calculating... [calculator:'+expression+']')


                answer = self.evaluate_expression(expression)
                answer = str(answer)

                new_prompt="This is an automatic response to your tool form. Please respond to the user's last message using the information below.\n\n"
                new_prompt += answer+"\n"

                self.ch.add_message_object('user', new_prompt)

            return answer

        else:
            return response_text


    def evaluate_expression(self, formula):
        """Evaluates mathematical expressions"""
        return eval(formula)

