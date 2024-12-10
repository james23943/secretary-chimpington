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
intents.members = True  # Add this line
bot = commands.Bot(command_prefix=None, intents=intents)  # New# Load cogs
async def load_extensions():
    cogs_path = Path(__file__).parent / 'cogs'
    for filename in os.listdir(cogs_path):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # Clear all existing commands
    bot.tree.clear_commands(guild=None)
    # Load new commands
    await load_extensions()
    # Sync changes
    await bot.tree.sync()  # Sync slash commands

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
