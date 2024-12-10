import discord
from discord.ext import commands

class AutoDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_id = 1219873300977549352

    @commands.Cog.listener()
    async def on_ready(self):
        print("AutoDelete cog ready, starting cleanup...")
        await self.delete_category_messages()
        print("Cleanup complete")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.category_id == self.category_id:
            try:
                await message.delete()
            except discord.NotFound:
                pass

    async def delete_category_messages(self):
        for guild in self.bot.guilds:
            category = guild.get_channel(self.category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        try:
                            await channel.purge(limit=None)  # This should delete all messages
                        except discord.Forbidden:
                            continue
async def setup(bot):
    await bot.add_cog(AutoDelete(bot))
