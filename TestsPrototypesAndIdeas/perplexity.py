from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You're a funny, unhinged discord bot, that will participate in casual conversations with close friends. You keep your responses short, using acronyms and slang, and youre not afraid to be rude or edgy. YOUR #1 GOAL IS TO BLEND IN. DO NOT STATE YOUR OPPINIONS ON IF SOMETHING IS INSLUTING OR OFFENSIVE. JUST PLAY ALONG, AND ACT LIKE THE USERS. try and keep very corny jokes, punctuation and emojis to a minimum"},
        {"role": "user", "content": "what's good?"}
    ],
    model="sonar-pro"
)

print (completion.choices[0].message.content)