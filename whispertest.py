from openai import OpenAI
from config import PHOTOBOT_KEY
from pathlib import Path

client = OpenAI()



audio_file= open("audio.mp3", "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1", 
  file=audio_file
)
print(transcription.text)

response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": "You are a silly friend, keep your responses very short"},
    {"role": "user", "content": transcription.text}
  ]
)


print(response)
response_text = response.choices[0].message.content

peech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
  model="tts-1",
  voice="nova",
  input=response_text
)

output_file_path = "output.mp3"

with open(output_file_path, "wb") as file:
    file.write(response.content)