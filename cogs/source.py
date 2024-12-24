import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio

class Source(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.COOLDOWN_DURATION = 5.0  # Seconds between command uses

    @app_commands.command(name="source", description="Get the link to the bot's source code and credits")
    async def source(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_time = discord.utils.utcnow().timestamp()
        
        # Handle cooldown
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
        credits = (
            "This bot, Secretary Chimpington, is open-source and available on GitHub.\n"
            f"Source Code: {github_link}\n\n"
            "Created by James. For more information, refer to the [README](https://github.com/james23943/secretary-chimpington/blob/main/README.md) "
            "and [LICENSE](https://github.com/james23943/secretary-chimpington/blob/main/LICENSE.md) files."
        )
        
        try:
            await interaction.response.send_message(credits)
        except discord.HTTPException:
            await asyncio.sleep(1)  # Rate limit backoff
            await interaction.response.send_message(credits)

async def setup(bot):
    await bot.add_cog(Source(bot))
