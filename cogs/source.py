import discord
from discord.ext import commands
from discord import app_commands

class Source(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="source", description="Get the link to the bot's source code and credits")
    async def source(self, interaction: discord.Interaction):
        github_link = "https://github.com/james23943/secretary-chimpington"
        credits = (
            "This bot, Secretary Chimpington, is open-source and available on GitHub.\n"
            f"Source Code: {github_link}\n\n"
            "Created by James. For more information, refer to the [README](https://github.com/james23943/secretary-chimpington/blob/main-v3/README.md) "
            "and [LICENSE](https://github.com/james23943/secretary-chimpington/blob/main-v3/LICENSE.md) files."
        )
        await interaction.response.send_message(credits)

async def setup(bot):
    await bot.add_cog(Source(bot))
