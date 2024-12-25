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