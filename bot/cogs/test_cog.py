from discord.ext import commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='testcommand', help='Test if command registration is working')
    async def test_command(self, ctx):
        await ctx.send('Test command is working!')

async def setup(bot):
    await bot.add_cog(TestCog(bot))
