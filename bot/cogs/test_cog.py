import discord
from discord.ext import commands
from discord import app_commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @app_commands.command(name='testcommand', description='Test if slash command registration is working')
    # async def test_command(self, interaction: discord.Interaction):
    #     await interaction.response.send_message('Slash command is working!')

async def setup(bot):
    await bot.add_cog(TestCog(bot))
