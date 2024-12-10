import discord
from discord.ext import commands

class AutoDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_id = 1219873300977549352

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.category_id == self.category_id:
            try:
                await message.delete()
            except discord.NotFound:
                pass

async def setup(bot):
    await bot.add_cog(AutoDelete(bot))
