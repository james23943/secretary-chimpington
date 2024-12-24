import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime
from pathlib import Path
import random
import asyncio
from typing import Dict

class LevelPageView(discord.ui.View):
    def __init__(self, pages, timeout=180):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()
            
    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels_path = Path(__file__).parent.parent / 'data' / 'levels.json'
        self.levels = self.load_levels()
        self.message_cooldowns: Dict[int, float] = {}
        self.command_cooldowns: Dict[int, float] = {}
        self.MESSAGE_COOLDOWN = 1.0
        self.COMMAND_COOLDOWN = 5.0

    def load_levels(self):
        try:
            with open(self.levels_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_levels(self):
        self.levels_path.parent.mkdir(exist_ok=True)
        with open(self.levels_path, 'w') as f:
            json.dump(self.levels, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        current_time = discord.utils.utcnow().timestamp()
        user_id = str(message.author.id)
        
        if user_id in self.message_cooldowns:
            if current_time - self.message_cooldowns[user_id] < self.MESSAGE_COOLDOWN:
                return
                
        self.message_cooldowns[user_id] = current_time
            
        if user_id not in self.levels:
            self.levels[user_id] = {"messages": 0, "level": 0}
            
        self.levels[user_id]["messages"] += 1
        new_level = self.levels[user_id]["messages"] // 100
        
        if new_level > self.levels[user_id]["level"]:
            self.levels[user_id]["level"] = new_level
            messages = [
                f"Oh look, {message.author.name} reached level {new_level}. How thrilling. 🎉",
                f"Against all odds, {message.author.name} made it to level {new_level}. 👏",
                f"Well well, {message.author.name} somehow got to level {new_level}. 🎈",
                f"*Slow clap* {message.author.name} reached level {new_level}. 🎊"
            ]
            try:
                await message.channel.send(random.choice(messages))
            except discord.HTTPException:
                await asyncio.sleep(1)
            
        await asyncio.sleep(0.1)
        self.save_levels()

    @app_commands.command(name="levelcheck", description="Check your current level")
    async def level_check(self, interaction: discord.Interaction):
        current_time = discord.utils.utcnow().timestamp()
        user_id = str(interaction.user.id)
        
        if user_id in self.command_cooldowns:
            remaining = self.COMMAND_COOLDOWN - (current_time - self.command_cooldowns[user_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"Command available in {remaining:.1f} seconds.",
                    ephemeral=True
                )
                return
                
        self.command_cooldowns[user_id] = current_time
        
        if user_id not in self.levels:
            await interaction.response.send_message("You haven't sent any messages yet!", ephemeral=True)
            return
            
        data = self.levels[user_id]
        await interaction.response.send_message(
            f"Level: {data['level']}\nMessages: {data['messages']}\nProgress to next level: {data['messages'] % 100}/100",
            ephemeral=True
        )

    @app_commands.command(name="levelleaderboard", description="View the level leaderboard")
    async def level_leaderboard(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            if not guild:
                return
                
            # Force member chunk request to ensure we have all members
            if not guild.chunked:
                await guild.chunk()
            
            current_members = {str(member.id): self.levels[str(member.id)]
                           for member in guild.members
                           if str(member.id) in self.levels}
            
            if not current_members:
                await interaction.response.send_message("No active members with levels found!", ephemeral=True)
                return
                
            sorted_levels = sorted(
                current_members.items(),
                key=lambda x: (x[1]['level'], x[1]['messages']),
                reverse=True
            )
            
            pages = []
            items_per_page = 30
            
            for i in range(0, len(sorted_levels), items_per_page):
                page_users = sorted_levels[i:i + items_per_page]
                
                description = "Send messages to gain levels!\n\n"
                for user_id, data in page_users:
                    user = interaction.guild.get_member(int(user_id))
                    if user:
                        safe_name = discord.utils.escape_markdown(user.name)
                        description += f"**Level {data['level']}**: {safe_name} ({data['messages']} messages)\n\n"
                
                embed = discord.Embed(
                    title="Level Leaderboard 📊",
                    description=description,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"📈 Page {i//items_per_page + 1}/{len(range(0, len(sorted_levels), items_per_page))} • Showing {len(page_users)} users • Total: {len(current_members)}")
                pages.append(embed)
            
            if not pages:
                await interaction.response.send_message("No data to display!", ephemeral=True)
                return
                
            try:
                await interaction.response.send_message(
                    embed=pages[0],
                    view=LevelPageView(pages) if len(pages) > 1 else None
                )
            except discord.HTTPException:
                await asyncio.sleep(1)
                await interaction.response.send_message(
                    embed=pages[0],
                    view=LevelPageView(pages) if len(pages) > 1 else None
                )
        except Exception as e:
            print(f"Error in levelleaderboard: {e}")
            await interaction.response.send_message("An error occurred while generating the leaderboard.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Levels(bot))