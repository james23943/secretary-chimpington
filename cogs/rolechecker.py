import discord
from discord.ext import commands

class RoleChecker(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.required_role_id = config['required_role_id']
        self.dependent_role_id = config['dependent_role_id']

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_roles_on_startup()

    async def check_roles_on_startup(self):
        for guild in self.bot.guilds:
            required_role = guild.get_role(self.required_role_id)
            dependent_role = guild.get_role(self.dependent_role_id)
            for member in guild.members:
                if dependent_role in member.roles and required_role not in member.roles:
                    await member.remove_roles(dependent_role)
                    try:
                        await member.send(
                            f"The role '{dependent_role.name}' requires you to have the '{required_role.name}' role. The role has been removed."
                        )
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
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
                pass

async def setup(bot):
    config = bot.config  # Assuming the config is stored in the bot instance
    await bot.add_cog(RoleChecker(bot, config))
