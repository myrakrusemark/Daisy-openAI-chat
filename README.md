## 🌼 Daisy.py 🌼
Daisy is a Python platform designed to work with language model APIs such as OpenAI's GPT-3 and GPT-4. It includes a suite of classes and methods that can be used to develop modules that can be dynamically added to extend and augment the reasoning capabilities of large language models. Notably, Daisy incorporates "tool-forms" that enable Daisy to utilize additional resources like web searching, context processing, memory/conversation review, calculations, and more.

### 🏁 Getting Started
Install necessary packages
```
pip install  -r  requirements.txt
```


Update ```config.py``` with necessary information and enable desired modules to be loaded.

Also, take a look at the individual module files to understand how they are loaded. You can make your own!
```
#Modules are loaded in the order they are listed here.
enabled_modules:
- modules.DanPrompt 
#Insert a DAN-like prompt to enable Daisy to "Do Anything Now"

- modules.DaisyPrompt 
#Give Daisy a few extra rules for behaving as a voice assistant

- modules.Daisy 
#Daisy voice assistant front-end

- modules.WebConfigDjango.WebConfigDjango
#Daisy web config tool based on Django

- modules.Dashboard_WebConfigDjango.Dashboard_WebConfigDjango
#Dynamically loaded route (new routes can be loaded through hooks as well)

#TTS Modules (Only the first one is loaded)
- modules.TtsElevenLabs
#TTS from ElevenLabs
- modules.GoogleCloudTTS
#TTS from ElevenLabs
- modules.GoogleTTS
#TTS from Google Translate TTS endpoint

- modules.GoogleScraper
#SerpAPI Google search result scraping tool

- modules.Calculator
#Python eval() to solve solvable expression strings

- modules.WeatherNoaaNl.WeatherNoaaNl
#Natural language to lat/lon weather forecast from NOAA.gov

- Memories
#Retrieve name/summary of all conversations in the sqlite DB

...See configs.yaml  or more configurations...
```


Run Daisy (platform)
```
py main.py
```

### 🧰 Capabilities
Daisy accepts different types of user-developed "modules". A voice assistant module comes with the project as a "proof-of-concept". Possible configurations and apps built using Daisy could include:
  - Web apps
  - Conversational processing APIs
  - Computer vision interpretation
  - Autonomous initiation (with time awareness, Daisy could send a message or tool-form without user input)
  - Customer service IVR (which could be powerful with API tool-forms on the back-end).
  - Possibilities are endless, you only need to create what you want to see in the world. This platform makes that easier.

Keep in mind: Daisy is still in development. It has, and will, evolve significantly in the coming months as contributors enhance functinality by improving platform code, ading module hooks, and developing their own modules.


### 🛎️ Services
Daisy uses the following APIs for conversation processing:
  - Language model: OpenAI chatGPT
  - Speech-to-text (STT): AssemblyAI
  - Text-To-Speech(TTS): ElevenLabs (Quality), Google Cloud TTS (Cheap), Google Translate TTS (Free!)
  - Wake word (Local): Picovice Porcupine
  - Alternative local APIs are available and should be easily interchangeable if you choose to use them. In some cases, they can be switched out as modules. In every other case, a code hook can be added to make it interchangeable.


### 🌇 Background
I have been eager to have a conversation with chatGPT using my voice. I used to search daily for a program that could exchange between speech recognition and TTS for a real human-like conversation, but it was not until recently that I discovered one.

So of course I began making what I wanted in the world. I started working on a voice recognition script for chatGPT. It began with simple requests, such as incorporating a request to openAI API and routing the speech recognition output. Since then the project evolved into a platform for building applications, opening the door for infinite potential.

Some people argue that text models and AI are not thinking, but just using heuristics. However, when we examine ourselves, we too are simply a collection of learned behavior and responses. Although GPT may not be perfect, it is important to reflect on ourselves and determine how much better we truly are.

### 🤝 Compatibility
This software is designed to run on Windows and Linux.


### ✅ To-Do
- LLMs (API or local) as modules
- Save and email contexts
- Manage load or export conversation contexts from WebConfig
- Get to know users. For instance, keep track of a persnality profile so you can begin to ask questions like "What would my wife like for her birthday?"
    - Using pyannote.audio to diarize speakers and identify them in each "user" message
    - Ask the AI to compare each message from a specific user to their personality profile and add new bits if it hears something new.
- Summarize and reset contexts when a conversation reaches max token value
