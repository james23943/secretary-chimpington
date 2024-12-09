import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)  # prefix doesn't matter for slash commands

# Load cogs
async def load_extensions():
    cogs_path = Path(__file__).parent / 'cogs'
    for filename in os.listdir(cogs_path):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await load_extensions()
    await bot.tree.sync()  # Sync slash commands

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
