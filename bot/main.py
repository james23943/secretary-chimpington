import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone  # Add timezoneimport json
import asyncio

# Load environment variables
load_dotenv()

import json

def load_last_online():
    try:
        with open('last_online.json', 'r') as f:
            return json.load(f)['timestamp']
    except FileNotFoundError:
        return 0

def save_last_online():
    with open('last_online.json', 'w') as f:
        json.dump({'timestamp': datetime.now(timezone.utc).timestamp()}, f)

async def periodic_save(bot):
    while not bot.is_closed():
        save_last_online()
        await asyncio.sleep(1)

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Add this line
bot = commands.Bot(command_prefix='/', intents=intents)  # New
async def load_extensions():
    cogs_path = Path(__file__).parent / 'cogs'
    for filename in os.listdir(cogs_path):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Cleanup category channels
    category_id = 1219873300977549352
    for guild in bot.guilds:
        category = guild.get_channel(category_id)
        if category and isinstance(category, discord.CategoryChannel):
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.purge(limit=None)
                        print(f"Cleaned channel: {channel.name}")
                    except discord.Forbidden:
                        print(f"No permission in: {channel.name}")

    # Continue with normal startup
    await load_extensions()
    await bot.tree.sync()
# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
