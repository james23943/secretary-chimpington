import discord
from discord.ext import commands

class RoleChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.required_role_id = 1191291888947437598
        self.dependent_role_id = 1311101869275484230

    @commands.Cog.listener()
    async def on_ready(self):
        # Check all members on startup
        for guild in self.bot.guilds:
            for member in guild.members:
                await self.check_roles(member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Check when roles change
        if before.roles != after.roles:
            await self.check_roles(after)

    async def check_roles(self, member):
        required_role = member.guild.get_role(self.required_role_id)
        dependent_role = member.guild.get_role(self.dependent_role_id)

        if dependent_role in member.roles and required_role not in member.roles:
            await member.remove_roles(dependent_role)
            try:
                await member.send(f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed.")
            except discord.Forbidden:
                pass  # Can't DM user

async def setup(bot):
    await bot.add_cog(RoleChecker(bot))
