## Daisy.py

Daisy is a platform designed to work with language model APIs such as OpenAI's chatGPT. It also incorporates "tool-forms" that enable Daisy to utilize additional resources like web searching, context processing, calculations, and more.

### Capabilities
Apart from in-situ modules, Daisy also accepts interchangeable front-end modules, making it quite versatile. It doesn't have to be a voice assistant; possible setups include:
  - Web app
  - Conversational processing API
  - Computer vision interpretation
  - Autonomous initiation (with time awareness, Daisy could send a message or tool-form without user input)
  - Customer service IVR (which could be powerful with API tool-forms on the back-end).
  - Possibilities are endless, you only need to create what you want to see in the world. This platform makes that easier.

It is worth noting that Daisy is still in development, and it can evolve significantly in terms of compatibility and functionality. However, the premise will always remain the same, and added capabilities will not be removed, although their functionality may change.


### Services
Daisy uses the following APIs for conversation processing:
  - Language model: OpenAI chatGPT
  - Speech-to-text (STT): AssemlyAI
  - Text-To-Speech(TTS): Google TTS
  - Wake word (Local): Picovice Porcupine
  - Alternatives, including offline, are available and should be easily interchangeable if you choose to use them. I plan to implement the above services as modules that can be easily cofigured.


### Background
I have been eager to have a conversation with chatGPT using my voice. I used to search daily for a program that could exchange between speech recognition and TTS for a real human-like conversation, but it was not until recently that I discovered one.

So of course I began making what I wanted in the world. I started working on a voice recognition script for chatGPT. It began with simple requests, such as incorporating a request to openAI API and routing the speech recognition output. At the end of the day, it felt like a complicated script that the text model AI couldn't handle, but every time I made changes, chatGPT would recognize and acknowledge my modifications.

One of the most surprising moments was when I included a self-written clrscr() function that added newline characters to clear the terminal output. ChatGPT recognized it and said, "It looks like you have added a function to clear the screen, which can provide a better user experience."

Some people argue that text models and AI are not thinking, but just using heuristics. However, when we examine ourselves, we too are simply a collection of learned behavior and responses. Although GPT-3.5 may not be perfect, it is important to reflect on ourselves and determine how much better we truly are.

### Compatibility
This software is designed to run on Windows and Raspberry Pi, as well as other ARM Linux implementations. This means you can easily repurpose an old desktop as a voice assistant using the Windows version, or use a Raspberry Pi to create a standalone voice assistant device.

I am also working on developing a case for the Pi (with WM8960 audio hat) and a breakout box for desktops, which will make it even easier to set up and use this software.


### To-Do
- Configure external services as modules
- Currently working on hardware (Raspberry PI case, Desktop breakout box)
- Save and email contexts
- Web UI configuration
    - Manage modules
    - Configure services (Language model, TTS/STT, wake word, etc)
    - Manage load or export conversation contexts
- Insert weather information start prompt
- Get to know users. For instance, keep track of a persnality profile so you can begin to ask questions like "What would my wife like for her birthday?"
    - Using pyannote.audio to diarize speakers and identify them in each "user" message
    - Ask the AI to compare each message from a specific user to their personality profile and add new bits if it hears something new.
- Summarize and reset contexts when a conversation reaches max token value
- Incorporate a prompt to encourage the use of SSML for adding emotional inflection to Daisy's responses
    - This is achievable and by using a DAN-style prompt, Daisy will generate outputs in SSML with appropriate emphasis.
