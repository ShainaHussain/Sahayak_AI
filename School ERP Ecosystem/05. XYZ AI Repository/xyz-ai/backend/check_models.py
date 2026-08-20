from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list()
    if not models.data:
        print("Key works but ZERO models available — account likely needs verification.")
    for m in models.data:
        print(m.id)
except Exception as e:
    print(f"Error: {e}")