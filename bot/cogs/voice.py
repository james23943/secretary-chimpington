import discord
from discord.ext import commands
import json

class VoiceChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_channel_id = 1187566046299832360
        self.blocked_role_id = 913372558693396511
        self.default_role_id = 1175949398564417627
        self.temp_channels = self.load_channels()
        
    def load_channels(self):
        try:
            with open('temp_channels.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_channels(self):
        with open('temp_channels.json', 'w') as f:
            json.dump(self.temp_channels, f)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Handle channel creation
        if after.channel and after.channel.id == self.create_channel_id:
            # Create channel permissions
            overwrites = {
                member: discord.PermissionOverwrite(move_members=True, manage_channels=True),
                member.guild.get_role(self.blocked_role_id): discord.PermissionOverwrite(view_channel=False),
                member.guild.get_role(self.default_role_id): discord.PermissionOverwrite(view_channel=True, connect=True)
            }
            
            # Create new channel
            new_channel = await member.guild.create_voice_channel(
                name=f"{member.name}'s Channel",
                category=after.channel.category,
                position=after.channel.position + 1,
                user_limit=10,
                overwrites=overwrites
            )
            
            # Move member to new channel
            await member.move_to(new_channel)
            
            # Save channel info
            self.temp_channels[str(new_channel.id)] = {
                "owner_id": member.id,
                "created_at": discord.utils.utcnow().timestamp()
            }
            self.save_channels()

        # Handle channel deletion
        if before.channel and str(before.channel.id) in self.temp_channels:
            if len(before.channel.members) == 0:
                await before.channel.delete()
                del self.temp_channels[str(before.channel.id)]
                self.save_channels()

    @commands.Cog.listener()
    async def on_ready(self):
        # Clean up empty channels on startup
        for guild in self.bot.guilds:
            for channel_id in list(self.temp_channels.keys()):
                channel = guild.get_channel(int(channel_id))
                if channel and len(channel.members) == 0:
                    await channel.delete()
                    del self.temp_channels[channel_id]
            self.save_channels()

async def setup(bot):
    await bot.add_cog(VoiceChannels(bot))
