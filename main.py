import discord
from discord.ext import commands
import os
from pathlib import Path
import asyncio
import json

# Get the absolute path to the bot's directory
BOT_DIR = Path(__file__).parent
CONFIG_PATH = BOT_DIR / 'config.json'

# Load config
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Bot setup with intents and enhanced settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Configure bot with optimal settings
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    max_messages=10000,
    chunk_guilds_at_startup=False,
    heartbeat_timeout=150.0,
)

# Add config to bot
bot.config = config

# Load cogs with error handling
async def load_extensions():
    cogs_dir = BOT_DIR / 'cogs'
    for filename in os.listdir(cogs_dir):
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
    except discord.HTTPException as e:
        print(f"Command sync rate limited. Retrying... Error: {e}")
        await asyncio.sleep(5)
        await bot.tree.sync()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f}s")
    elif isinstance(error, commands.CommandRateLimit):
        await ctx.send("We're being rate limited. Please wait a moment.")

# Run the bot with automatic reconnection
bot.run(
    config['bot_token'],
    reconnect=True,
    log_handler=None
)
