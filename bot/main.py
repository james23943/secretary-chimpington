import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio

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
                await asyncio.sleep(0.5)  # Prevent rate limiting during startup
            except Exception as e:
                print(f'Failed to load extension {filename}: {e}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Batch process startup tasks
    async def startup_tasks():
        # Cleanup category channels
        category_id = 1219873300977549352
        for guild in bot.guilds:
            category = guild.get_channel(category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        try:
                            await channel.purge(limit=None)
                            await asyncio.sleep(1)  # Rate limit prevention
                            print(f"Cleaned channel: {channel.name}")
                        except discord.Forbidden:
                            print(f"No permission in: {channel.name}")

        # Check roles with rate limiting
        required_role_id = 1191291888947437598
        dependent_role_id = 1311101869275484230
        for guild in bot.guilds:
            required_role = guild.get_role(required_role_id)
            dependent_role = guild.get_role(dependent_role_id)
            for member in guild.members:
                if dependent_role in member.roles and required_role not in member.roles:
                    await member.remove_roles(dependent_role)
                    await asyncio.sleep(0.5)  # Rate limit prevention
                    try:
                        await member.send(f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed.")
                    except discord.Forbidden:
                        pass

        # Load and sync commands
        await load_extensions()
        await bot.tree.sync()

    # Run startup tasks
    await startup_tasks()

# Run the bot with reconnect enabled
bot.run(os.getenv('DISCORD_TOKEN'), reconnect=True)
