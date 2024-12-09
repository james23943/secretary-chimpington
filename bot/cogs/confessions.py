import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path

class ConfessionReplyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Reply", style=discord.ButtonStyle.blurple)
    
    async def callback(self, interaction: discord.Interaction):
        thread_name = f"Replies to {interaction.message.embeds[0].title}"
        thread = await interaction.message.create_thread(name=thread_name)
        await interaction.response.send_message(f"Created thread for replies!", ephemeral=True)

class ConfessionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConfessionReplyButton())

class Confessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.confession_count = self.load_count()
        self.confession_channel_id = 1176076931217756180
    
    def load_count(self):
        try:
            with open('confession_count.json', 'r') as f:
                data = json.load(f)
                return data.get('count', 478)  # Start at 478 so next is 479
        except FileNotFoundError:
            self.save_count(478)
            return 478
    
    def save_count(self, count):
        with open('confession_count.json', 'w') as f:
            json.dump({'count': count}, f)
    
    @app_commands.command(name="confess", description="Submit an anonymous confession")
    async def confess(self, interaction: discord.Interaction, confession: str):
        # Check if command is used in correct channel
        if interaction.channel_id != self.confession_channel_id:
            await interaction.response.send_message(
                "This command can only be used in the confessions channel!", 
                ephemeral=True
            )
            return
        
        self.confession_count += 1
        self.save_count(self.confession_count)
        
        # Create and send embed
        embed = discord.Embed(
            title=f"Confession #{self.confession_count}",
            description=confession,
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(
            "Your confession has been submitted!", 
            ephemeral=True
        )
        await interaction.channel.send(embed=embed, view=ConfessionView())

async def setup(bot):
    await bot.add_cog(Confessions(bot))
