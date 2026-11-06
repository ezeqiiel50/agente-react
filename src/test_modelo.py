import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

modelos = [
    m.name.removeprefix("models/")
    for m in client.models.list()
    if "generateContent" in (m.supported_actions or [])
    and "flash" in m.name
    and "image" not in m.name
    and "tts" not in m.name
]
print("Candidatos:", modelos, "\n")

for nombre in modelos[:8]:
    t0 = time.perf_counter()
    try:
        r = client.models.generate_content(model=nombre, contents="Decime hola en una palabra")
        print(f"OK   {nombre:40s} {time.perf_counter() - t0:5.1f}s -> {r.text.strip()}")
    except Exception as e:
        print(f"FAIL {nombre:40s} {time.perf_counter() - t0:5.1f}s -> {str(e)[:90]}")