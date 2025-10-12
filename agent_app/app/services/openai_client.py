import os
from openai import OpenAI
client = OpenAI(base_url=os.environ["NIM_API_BASE"], api_key=os.environ["NIM_API_KEY"])