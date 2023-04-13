from datetime import datetime
import os

cwd = os.path.dirname(os.path.abspath(__file__))+"/"

#Initial prompts
#an be optionally passed to chat()
start_prompt_Daisy = ""
#Build start prompt     
messages=[{"role": "user", "timestamp":"", "content": start_prompt_Daisy}]