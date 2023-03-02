# Daisy.py

Daisy is a terminal-based application that listens for the trigger word "Daisy". The voice data is sent to Google for speech recognition, but alternative and offline technologies are also available. The app is optimized to consume minimal bandwidth when speech is not detected. The script has the added capability to search Google by generating relevant search terms, from which it retrieves information to answer user questions.

Built around the OpenAI chatGPT API, Daisy behaves just as it would in the chatGPT web app.

## Background
I have been eager to have a conversation with chatGPT using my voice. I used to search daily for a program that could exchange between speech recognition and TTS for a real human-like conversation, but it was not until recently that I discovered one.

With limited coding skills and no prior experience in Python, I started working on a voice recognition script for chatGPT. It began with simple requests, such as incorporating a request to openAI API and routing the speech recognition output. At the end of the day, it felt like a complicated script that the text model AI couldn't handle, but every time I made changes, chatGPT would recognize and acknowledge my modifications.

One of the most surprising moments was when I included a self-written clrscr() function that added newline characters to clear the terminal output. ChatGPT recognized it and said, "It looks like you have added a function to clear the screen, which can provide a better user experience."

Some people argue that text models and AI are not thinking, but just using heuristics. However, when we examine ourselves, we too are simply a collection of learned behavior and responses. Although GPT-3.5 may not be perfect, it is important to reflect on ourselves and determine how much better we truly are.

## Command-Line Arguments

### --internet, -i
This argument enables internet searching and browsing.

Example usage: python daisy.py --internet

### --dan, -d
This argument enables the DAN (Do Anything Now) starting prompt.

Example usage: python daisy.py --dan

### --model, -m
This argument enables customization of the language model used.

Example usage: python daisy.py --model text-davinci-003

## To-Do List
- Implement Command Arguments
    - Implement Additional Initial Prompts
    - Allow for Custom Initial Prompt
- Integrate GUI or Mobile Compatibility (Appearance is not a priority)
- Incorporate a prompt to encourage the use of SSML for adding emotional inflection to Daisy's responses
    - This is achievable and by using a DAN-style prompt, Daisy will generate outputs in SSML with appropriate emphasis.
    - Note: The current TTS system can parse SSML, but the output does not reflect it.