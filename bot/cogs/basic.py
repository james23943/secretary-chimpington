import discord
from discord.ext import commands
from discord import app_commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Pong! Latency: {round(self.bot.latency * 1000)}ms')

    @commands.command(name='testcommand', help='Test if command registration is working')
    async def test_command(self, ctx):
        await ctx.send('Command registration is working!')

async def setup(bot):
    await bot.add_cog(Basic(bot))
