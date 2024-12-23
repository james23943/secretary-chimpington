import discord
from discord.ext import commands
import json
from pathlib import Path
import os

# Load configuration
config_path = Path(__file__).parent / 'config.json'  # Ensure this path is correct
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

async def load_extensions():
    cogs_path = Path(__file__).parent / 'cogs'
    for filename in os.listdir(cogs_path):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception as e:
                print(f'Failed to load extension {filename}: {e}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await load_extensions()
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

# Run the bot
bot.run(config['bot_token'])