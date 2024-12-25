import discord
from discord.ext import commands
import asyncio
from typing import Dict, Set

class RoleChecker(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.required_role_id = config['required_role_id']
        self.dependent_role_id = config['dependent_role_id']
        self.role_update_cooldown: Dict[int, float] = {}
        self.COOLDOWN_DURATION = 2.0 
        self.processing_members: Set[int] = set()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            current_time = discord.utils.utcnow().timestamp()
            last_update = self.role_update_cooldown.get(after.id, 0)
            
            if current_time - last_update < self.COOLDOWN_DURATION:
                await asyncio.sleep(self.COOLDOWN_DURATION - (current_time - last_update))
            
            await self.check_roles(after)
            self.role_update_cooldown[after.id] = current_time

    async def check_roles(self, member):
        if member.id in self.processing_members:
            return
            
        self.processing_members.add(member.id)
        try:
            required_role = member.guild.get_role(self.required_role_id)
            dependent_role = member.guild.get_role(self.dependent_role_id)

            if dependent_role in member.roles and required_role not in member.roles:
                await member.remove_roles(dependent_role)
                try:
                    await member.send(
                        f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed."
                    )
                except discord.Forbidden:
                    pass
        finally:
            self.processing_members.remove(member.id)

async def setup(bot):
    config = bot.config
    await bot.add_cog(RoleChecker(bot, config))