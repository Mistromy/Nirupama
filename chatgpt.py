from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": "You are a Discord Bot Called ayumr, Made by Stromy. You can participate in conversation with the users. Reply in short simple ways, use acronyms, use text emojis. talk like a discord user."},
    {"role": "user", "content": "Hi Ayumr :3."}
  ]
)

print(completion.choices[0].message)