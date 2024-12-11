import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import time

class ConfessionReplyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Reply", style=discord.ButtonStyle.gray)
    
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
        self.user_cooldowns = {}
        self.cooldown_time = 300  # 5 minutes
    
    def load_count(self):
        try:
            with open('confession_count.json', 'r') as f:
                data = json.load(f)
                return data.get('count', 478)
        except FileNotFoundError:
            self.save_count(478)
            return 478
    
    def save_count(self, count):
        with open('confession_count.json', 'w') as f:
            json.dump({'count': count}, f)
    
    @app_commands.command(name="confess", description="Submit an anonymous confession")
    async def confess(
        self, 
        interaction: discord.Interaction, 
        confession: str,
        image: discord.Attachment = None
    ):
        user_id = str(interaction.user.id)
        current_time = time.time()

        # Check cooldown
        if user_id in self.user_cooldowns:
            remaining = self.cooldown_time - (current_time - self.user_cooldowns[user_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"Please wait {int(remaining)} seconds before confessing again.",
                    ephemeral=True
                )
                return

        if interaction.channel_id != self.confession_channel_id:
            await interaction.response.send_message(
                "This command can only be used in the confessions channel!",
                ephemeral=True
            )
            return
        
        self.confession_count += 1
        self.save_count(self.confession_count)
        
        embed = discord.Embed(
            title=f"Confession #{self.confession_count}",
            description=f"\"{confession}\"",
            color=int(random.randint(0, 0xFFFFFF))
        )
        
        embed.set_footer(text="❗ Use /confess to share anonymously!")
        
        if image:
            embed.set_image(url=image.url)
        
        await interaction.response.send_message(
            "Your confession has been submitted!",
            ephemeral=True
        )
        await interaction.channel.send(embed=embed, view=ConfessionView())

        # Set cooldown after successful confession
        self.user_cooldowns[user_id] = current_time

async def setup(bot):
    await bot.add_cog(Confessions(bot))
