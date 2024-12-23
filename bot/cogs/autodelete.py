import discord
from discord.ext import commands

class AutoDelete(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.category_id = config['category_id']

    @commands.Cog.listener()
    async def on_ready(self):
        await self.cleanup_category_channels()

    async def cleanup_category_channels(self):
        for guild in self.bot.guilds:
            category = guild.get_channel(self.category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        try:
                            await channel.purge(limit=None)
                        except discord.Forbidden:
                            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            return
        if message.channel.category_id == self.category_id:
            try:
                await message.delete()
            except discord.NotFound:
                pass

async def setup(bot):
    config = bot.config  # Assuming the config is stored in the bot instance
    await bot.add_cog(AutoDelete(bot, config))
