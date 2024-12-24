import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict
import asyncio

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns: Dict[int, float] = {}
        self.COOLDOWN_DURATION = 3.0  # Seconds between ping checks

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_time = discord.utils.utcnow().timestamp()
        
        # Handle cooldown
        if user_id in self.cooldowns:
            remaining = self.COOLDOWN_DURATION - (current_time - self.cooldowns[user_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"Ping will be available in {remaining:.1f} seconds.", 
                    ephemeral=True
                )
                return

        self.cooldowns[user_id] = current_time
        
        try:
            latency = round(self.bot.latency * 1000)
            await interaction.response.send_message(f'Pong! Latency: {latency}ms')
        except discord.HTTPException:
            await asyncio.sleep(1)  # Rate limit backoff
            await interaction.response.send_message('Pong! (Latency check delayed)')

async def setup(bot):
    await bot.add_cog(Ping(bot))
