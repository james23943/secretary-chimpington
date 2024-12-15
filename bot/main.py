import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import time

# Load environment variables
load_dotenv()

# Bot setup with optimized intents
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
                await asyncio.sleep(2)  # Delay to prevent rate limits
            except Exception as e:
                print(f'Failed to load extension {filename}: {e}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    async def startup_tasks():
        await asyncio.sleep(5)  # Initial delay before tasks
        
        # Cleanup category channels with rate limiting
        category_id = 1219873300977549352
        for guild in bot.guilds:
            category = guild.get_channel(category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        try:
                            await channel.purge(limit=None)
                            await asyncio.sleep(2)  # Increased delay
                            print(f"Cleaned channel: {channel.name}")
                        except discord.Forbidden:
                            print(f"No permission in: {channel.name}")

        await asyncio.sleep(5)  # Delay between major tasks

        # Role checks with enhanced rate limiting
        required_role_id = 1191291888947437598
        dependent_role_id = 1311101869275484230
        for guild in bot.guilds:
            required_role = guild.get_role(required_role_id)
            dependent_role = guild.get_role(dependent_role_id)
            for member in guild.members:
                if dependent_role in member.roles and required_role not in member.roles:
                    try:
                        await member.remove_roles(dependent_role)
                        await asyncio.sleep(1.5)  # Increased delay for role operations
                        try:
                            await member.send(f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed.")
                            await asyncio.sleep(1)  # DM rate limiting
                        except discord.Forbidden:
                            pass
                    except discord.HTTPException:
                        await asyncio.sleep(5)  # Backoff on rate limit

        await asyncio.sleep(5)  # Delay before extensions

        # Load and sync commands
        await load_extensions()
        await asyncio.sleep(2)
        try:
            await bot.tree.sync()
            print("Slash commands synced successfully.")
        except Exception as e:
            print(f"Failed to sync slash commands: {e}")

    # Run startup tasks with retry mechanism
    retries = 0
    while retries < 3:
        try:
            await startup_tasks()
            break
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limit
                retries += 1
                await asyncio.sleep(10 * retries)
            else:
                raise e

# Run bot with enhanced reconnection handling
def run_with_backoff():
    retries = 0
    while retries < 5:
        try:
            bot.run(os.getenv('DISCORD_TOKEN'), reconnect=True)
            break
        except discord.errors.HTTPException as e:
            if e.status == 429:
                retries += 1
                time.sleep(10 * retries)
            else:
                raise e

run_with_backoff()
