import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio

# Load environment variables
load_dotenv()

# Bot setup with intents and enhanced settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Configure bot with optimal settings
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    max_messages=10000,  # Cache more messages to reduce API calls
    chunk_guilds_at_startup=False,  # Defer member chunking for better startup
    heartbeat_timeout=150.0,  # Increase heartbeat timeout for stability
)

# Load cogs with error handling
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception as e:
                print(f'Failed to load extension {filename}: {e}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await load_extensions()
    
    # Rate limit safe command sync
    try:
        await bot.tree.sync()
    except discord.HTTPException as e:
        print(f"Command sync rate limited. Retrying... Error: {e}")
        await asyncio.sleep(5)  # Wait before retry
        await bot.tree.sync()

# Global rate limit handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f}s")
    elif isinstance(error, commands.CommandRateLimit):
        await ctx.send("We're being rate limited. Please wait a moment.")

# Run the bot with automatic reconnection
bot.run(
    os.getenv('DISCORD_TOKEN'),
    reconnect=True,
    log_handler=None  # Disable default logging for cleaner output
)
