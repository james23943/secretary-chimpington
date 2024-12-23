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
                        print(f"No permission to clean: {channel.name}")

    # Check roles on startup
    required_role_id = 1191291888947437598
    dependent_role_id = 1311101869275484230
    for guild in bot.guilds:
        required_role = guild.get_role(required_role_id)
        dependent_role = guild.get_role(dependent_role_id)
        for member in guild.members:
            if dependent_role in member.roles and required_role not in member.roles:
                await member.remove_roles(dependent_role)
                try:
                    await member.send(
                        f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed."
                    )
                except discord.Forbidden:
                    print(f"Could not send message to {member.name}")

    # Load extensions and sync commands
    await load_extensions()
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
