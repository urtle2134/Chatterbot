import discord
import os
import random
import requests
from dotenv import load_dotenv
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("")
WEATHER_API_KEY = os.getenv("894ee1265a1bd01ecefba659d4eee27c")

# Setup chatbot with persistent storage
chatbot = ChatBot(
    "Motivator",
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    database_uri='sqlite:///database.sqlite3'
)

# Train with some motivational data and general greetings
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english.greetings", "chatterbot.corpus.english.conversations")

custom_motivation = [
    "I feel down.",
    "You are strong and capable. Keep moving forward!",
    "I failed.",
    "Failure is the first step to success!",
    "I'm not good enough.",
    "Yes you are. You have everything you need to succeed.",
    "I can't do it.",
    "You can. Progress takes time, don’t give up."
]
list_trainer = ListTrainer(chatbot)
list_trainer.train(custom_motivation)

# Set up Discord client
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

channel_context = {}
banned_words = ["hate", "jealous"]
auto_responses = {
    "how do i stay motivated": "Set small goals and celebrate your progress!",
    "help": "Try `!motivate`, `!joke`, or `!weather <city>` for some help!"
}

# Joke API
def get_joke():
    try:
        res = requests.get("https://official-joke-api.appspot.com/random_joke").json()
        return f"{res['setup']} ... {res['punchline']}"
    except:
        return "Couldn't fetch a joke right now!"

# Weather API
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()
        return f"{data['weather'][0]['description'].capitalize()}, {data['main']['temp']}°C in {city}."
    except:
        return "Couldn't fetch weather right now."

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Keyword Filtering
    for word in banned_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention}, that word is not allowed.")
            return

    # Auto responses
    for key in auto_responses:
        if key in message.content.lower():
            await message.channel.send(auto_responses[key])
            return

    channel_id = str(message.channel.id)
    if channel_id not in channel_context:
        channel_context[channel_id] = []

    # Dynamic Commands
    if message.content.startswith("!joke"):
        await message.channel.send(get_joke())
        return

    if message.content.startswith("!weather"):
        city = message.content.replace("!weather", "").strip()
        await message.channel.send(get_weather(city or "London"))
        return

    if message.content.startswith("!motivate") or client.user.mentioned_in(message):
        user_input = message.content.replace("!motivate", "").strip()
        channel_context[channel_id].append((message.author.name, user_input))

        if not user_input:
            await message.channel.send(random.choice([
                "You’ve got this!",
                "Keep moving forward!",
                "Every step counts. You're doing great!",
                "Your effort matters more than perfection!"
            ]))
        else:
            response = chatbot.get_response(user_input)
            chatbot.learn_response(response, user_input)  # Learn from conversation
            await message.channel.send(str(response))

client.run(DISCORD_TOKEN)
