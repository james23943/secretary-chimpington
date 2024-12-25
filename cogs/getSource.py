import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio

class Source(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.COOLDOWN_DURATION = 5.0

    @app_commands.command(name="source", description="Get the link to the bot's source code and credits")
    async def source(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_time = discord.utils.utcnow().timestamp()

        if user_id in self.cooldowns:
            remaining = self.COOLDOWN_DURATION - (current_time - self.cooldowns[user_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"This command will be available in {remaining:.1f} seconds.", 
                    ephemeral=True
                )
                return

        self.cooldowns[user_id] = current_time
        
        github_link = "https://github.com/james23943/secretary-chimpington"
        
        embed = discord.Embed(
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="GitHub Repository",
            value=f"[Click here to view the source code]({github_link})",
            inline=False
        )
        
        try:
            await interaction.response.send_message(embed=embed)
        except discord.HTTPException:
            await asyncio.sleep(1)
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Source(bot))
