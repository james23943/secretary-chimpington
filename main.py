import discord
from discord.ext import commands
import os
from pathlib import Path
import asyncio
import json

# Get the absolute path to the bot's directory
BOT_DIR = Path(__file__).parent
CONFIG_PATH = BOT_DIR / 'config.json'
DATA_PATH = BOT_DIR / 'data'

# Load config
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Bot setup with intents and enhanced settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Configure bot with optimal settings
bot = commands.Bot(
    command_prefix='/',
    intents=intents,
    max_messages=10000,
    chunk_guilds_at_startup=False,
    heartbeat_timeout=150.0,
)

# Add config to bot
bot.config = config

async def cleanup_temp_channels():
    temp_channels_path = DATA_PATH / 'temp_channels.json'
    if temp_channels_path.exists():
        with open(temp_channels_path, 'r') as f:
            temp_channels = json.load(f)
        for channel_id in list(temp_channels.keys()):
            channel = bot.get_channel(int(channel_id))
            if channel and len(channel.members) == 0:
                await channel.delete()
                del temp_channels[channel_id]
        with open(temp_channels_path, 'w') as f:
            json.dump(temp_channels, f)

async def verify_roles():
    for guild in bot.guilds:
        for member in guild.members:
            required_role = guild.get_role(config['required_role_id'])
            dependent_role = guild.get_role(config['dependent_role_id'])
            if dependent_role in member.roles and required_role not in member.roles:
                await member.remove_roles(dependent_role)

async def clear_category_messages():
    for guild in bot.guilds:
        category = guild.get_channel(config['category_id'])
        if category:
            for channel in category.text_channels:
                async for message in channel.history():
                    await message.delete()
                    await asyncio.sleep(0.5)

async def startup_tasks():
    await bot.wait_until_ready()
    await cleanup_temp_channels()
    await verify_roles()
    await clear_category_messages()

# Load cogs with error handling
async def load_extensions():
    cogs_dir = BOT_DIR / 'cogs'
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception as e:
                pass

@bot.event
async def on_ready():
    await load_extensions()
    bot.loop.create_task(startup_tasks())
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
