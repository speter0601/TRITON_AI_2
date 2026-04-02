import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")