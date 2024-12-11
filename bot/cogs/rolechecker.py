import discord
from discord.ext import commands
import asyncio
from collections import deque

class RoleChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.required_role_id = 1191291888947437598
        self.dependent_role_id = 1311101869275484230
        self.role_update_queue = deque()
        self.processing = False
        self.bot.loop.create_task(self.process_role_updates())

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            self.role_update_queue.append(after)
            if not self.processing:
                self.processing = True
                await self.process_role_updates()

    async def process_role_updates(self):
        while self.role_update_queue:
            member = self.role_update_queue.popleft()
            required_role = member.guild.get_role(self.required_role_id)
            dependent_role = member.guild.get_role(self.dependent_role_id)

            if dependent_role in member.roles and required_role not in member.roles:
                try:
                    await member.remove_roles(dependent_role)
                    await asyncio.sleep(1)  # Rate limit prevention
                    try:
                        await member.send(f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed.")
                    except discord.Forbidden:
                        pass
                except discord.HTTPException:
                    await asyncio.sleep(5)  # Backoff on API errors
                    self.role_update_queue.append(member)  # Retry later

        self.processing = False

async def setup(bot):
    await bot.add_cog(RoleChecker(bot))
