import discord
from discord.ext import commands
from discord import app_commands
import time

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_cooldowns = {}
        self.cooldown_time = 5  # 5 second cooldown
    
    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        current_time = time.time()

        if user_id in self.command_cooldowns:
            if current_time - self.command_cooldowns[user_id] < self.cooldown_time:
                await interaction.response.send_message("Command on cooldown. Please wait.", ephemeral=True)
                return

        self.command_cooldowns[user_id] = current_time
        await interaction.response.send_message(f'Pong! Latency: {round(self.bot.latency * 1000)}ms')

async def setup(bot):
    await bot.add_cog(Basic(bot))
