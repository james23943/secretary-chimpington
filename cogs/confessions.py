import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path
import random
import emoji
from typing import Dict
import asyncio

class ConfessionReplyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Reply", style=discord.ButtonStyle.blurple)
    
    async def callback(self, interaction: discord.Interaction):
        thread_name = f"Replies to {interaction.message.embeds[0].title}"
        try:
            thread = await interaction.message.create_thread(name=thread_name)
            await interaction.response.send_message(f"Created thread for replies!", ephemeral=True)
        except discord.HTTPException:
            await asyncio.sleep(1)
            thread = await interaction.message.create_thread(name=thread_name)
            await interaction.response.send_message(f"Created thread for replies!", ephemeral=True)

class ConfessionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConfessionReplyButton())

class Confessions(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.confession_count_path = Path(__file__).parent.parent / 'data' / 'confession_count.json'
        self.confession_count = self.load_count()
        self.confession_channel_id = config['confession_channel_id']
        self.emojis = list(emoji.EMOJI_DATA.keys())
        self.cooldowns: Dict[int, float] = {}
        self.COOLDOWN_DURATION = 5.0
    
    def load_count(self):
        try:
            with open(self.confession_count_path, 'r') as f:
                data = json.load(f)
                return data.get('count', 0)
        except FileNotFoundError:
            self.save_count(0)
            return 0
    
    def save_count(self, count):
        with open(self.confession_count_path, 'w') as f:
            json.dump({'count': count}, f)
    
    @app_commands.command(name="confess", description="Submit an anonymous confession")
    async def confess(
        self, 
        interaction: discord.Interaction, 
        confession: str,
        image: discord.Attachment = None
    ):
        current_time = discord.utils.utcnow().timestamp()
        user_id = interaction.user.id

        if interaction.channel_id != self.confession_channel_id:
            await interaction.response.send_message(
                "This command can only be used in the confessions channel!",
                ephemeral=True
            )
            return

        if user_id in self.cooldowns:
            remaining = self.COOLDOWN_DURATION - (current_time - self.cooldowns[user_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"You can confess again in {remaining:.1f} seconds.",
                    ephemeral=True
                )
                return

        self.cooldowns[user_id] = current_time
        self.confession_count += 1
        self.save_count(self.confession_count)
        
        embed = discord.Embed(
            title=f"Confession #{self.confession_count}",
            description=f"\"{confession}\"",
            color=discord.Color.random()
        )
        
        random_emoji = random.choice(self.emojis)
        embed.set_footer(text=random_emoji)
        
        if image:
            embed.set_image(url=image.url)
        
        await interaction.response.send_message(
            "Your confession has been submitted!",
            ephemeral=True
        )

        try:
            await interaction.channel.send(embed=embed, view=ConfessionView())
        except discord.HTTPException:
            await asyncio.sleep(1)
            await interaction.channel.send(embed=embed, view=ConfessionView())

async def setup(bot):
    config = bot.config
    await bot.add_cog(Confessions(bot, config))
