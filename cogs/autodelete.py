import discord
from discord.ext import commands
import asyncio
from typing import Dict, Set

class AutoDelete(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.category_id = config['category_id']
        self.delete_cooldowns: Dict[int, float] = {}
        self.processing_channels: Set[int] = set()
        self.COOLDOWN_DURATION = 1.0
        self.BULK_DELETE_DELAY = 2.0

    @commands.Cog.listener()
    async def on_ready(self):
        await self.cleanup_category_channels()

    async def cleanup_category_channels(self):
        await asyncio.sleep(5)  # Initial delay for bot to fully initialize
        
        for guild in self.bot.guilds:
            category = guild.get_channel(self.category_id)
            if category and isinstance(category, discord.CategoryChannel):
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        if channel.id in self.processing_channels:
                            continue
                            
                        self.processing_channels.add(channel.id)
                        try:
                            async for batch in self.batch_delete_messages(channel):
                                await asyncio.sleep(self.BULK_DELETE_DELAY)
                        finally:
                            self.processing_channels.remove(channel.id)

    async def batch_delete_messages(self, channel):
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
                
        messages = []
        async for message in channel.history(limit=None):
            messages.append(message)
            if len(messages) >= 100:
                yield messages
                messages = []
        if messages:
            yield messages

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            return
            
        if message.channel.category_id == self.category_id:
            current_time = discord.utils.utcnow().timestamp()
            
            if message.channel.id in self.delete_cooldowns:
                if current_time - self.delete_cooldowns[message.channel.id] < self.COOLDOWN_DURATION:
                    await asyncio.sleep(self.COOLDOWN_DURATION)
                    
            try:
                await message.delete()
                self.delete_cooldowns[message.channel.id] = current_time
            except (discord.NotFound, discord.Forbidden):
                pass
            except discord.HTTPException:
                await asyncio.sleep(1)
                try:
                    await message.delete()
                except:
                    pass

async def setup(bot):
    config = bot.config
    await bot.add_cog(AutoDelete(bot, config))
