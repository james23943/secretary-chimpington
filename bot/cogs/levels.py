import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime
import random
import time

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
        self.levels = self.load_levels()
        self.level_cooldowns = {}
        self.command_cooldowns = {}
    
    def load_levels(self):
        try:
            with open('levels.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_levels(self):
        with open('levels.json', 'w') as f:
            json.dump(self.levels, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        user_id = str(message.author.id)
        current_time = time.time()

        # Check cooldown for level up messages
        if user_id in self.level_cooldowns:
            if current_time - self.level_cooldowns[user_id] < 60:
                return
            
        if user_id not in self.levels:
            self.levels[user_id] = {"messages": 0, "level": 0}
            
        self.levels[user_id]["messages"] += 1
        new_level = self.levels[user_id]["messages"] // 100
        
        if new_level > self.levels[user_id]["level"]:
            self.levels[user_id]["level"] = new_level
            self.level_cooldowns[user_id] = current_time
            
            messages = [
                f"Oh look, {message.author.name} reached level {new_level}. How thrilling. 🎉",
                f"Against all odds, {message.author.name} made it to level {new_level}. 👏",
                f"Well well, {message.author.name} somehow got to level {new_level}. 🎈",
                f"*Slow clap* {message.author.name} reached level {new_level}. 🎊"
            ]
            await message.channel.send(random.choice(messages))
            
        self.save_levels()

    @app_commands.command(name="levelcheck", description="Check your current level")
    async def level_check(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        current_time = time.time()

        # Check command cooldown
        if user_id in self.command_cooldowns:
            if current_time - self.command_cooldowns[user_id] < 30:
                await interaction.response.send_message("Please wait before using this command again.", ephemeral=True)
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
        current_time = time.time()

        # Check command cooldown
        if 'leaderboard' in self.command_cooldowns:
            if current_time - self.command_cooldowns['leaderboard'] < 30:
                await interaction.response.send_message("Please wait before using this command again.", ephemeral=True)
                return

        self.command_cooldowns['leaderboard'] = current_time

        if not self.levels:
            await interaction.response.send_message("No levels recorded yet!", ephemeral=True)
            return
            
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Could not find server!", ephemeral=True)
            return
            
        current_members = {str(member.id): self.levels[str(member.id)] 
                         for member in guild.members 
                         if str(member.id) in self.levels}
        
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
        
        await interaction.response.send_message(
            embed=pages[0],
            view=LevelPageView(pages) if len(pages) > 1 else None
        )

async def setup(bot):
    await bot.add_cog(Levels(bot))
