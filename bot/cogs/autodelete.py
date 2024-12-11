import discord
from discord.ext import commands
import asyncio
from collections import deque

class AutoDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_id = 1219873300977549352
        self.delete_queue = deque()
        self.processing = False
        self.bot.loop.create_task(self.process_delete_queue())

    @commands.Cog.listener()
    async def on_message(self, message):
        # Skip DM channels
        if not isinstance(message.channel, discord.TextChannel):
            return
            
        if message.channel.category_id == self.category_id:
            self.delete_queue.append(message)

    async def process_delete_queue(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if self.delete_queue:
                message = self.delete_queue.popleft()
                try:
                    await message.delete()
                    await asyncio.sleep(1)  # Rate limit prevention
                except discord.NotFound:
                    pass
                except discord.HTTPException:
                    await asyncio.sleep(5)  # Longer delay on API errors
            else:
                await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(AutoDelete(bot))
