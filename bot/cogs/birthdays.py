import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime, timedelta
import pytz
from typing import Optional
import asyncio

class BirthdayPageView(discord.ui.View):
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

class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays = self.load_birthdays()
        self.birthday_role_id = 1217828559742173246
        self.birthday_channel_id = 1209482944176201738
        self.active_birthday_roles = self.load_active_roles()
        self.bot.loop.create_task(self.birthday_check_loop())
    
    def load_birthdays(self):
        try:
            with open('birthdays.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_birthdays(self):
        with open('birthdays.json', 'w') as f:
            json.dump(self.birthdays, f)
    
    def load_active_roles(self):
        try:
            with open('active_birthday_roles.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_active_roles(self):
        with open('active_birthday_roles.json', 'w') as f:
            json.dump(self.active_birthday_roles, f)

    @app_commands.command(name="birthday", description="Set your birthday")
    @app_commands.describe(
        day="Day of your birthday (1-31)",
        month="Month of your birthday (1-12)",
        timezone="Your timezone (Example: UTC+10, America/New_York)"
    )
    async def birthday(
        self,
        interaction: discord.Interaction,
        day: int,
        month: int,
        timezone: str
    ):
        if interaction.channel_id != self.birthday_channel_id:
            await interaction.response.send_message(
                "This command can only be used in the birthdays channel!",
                ephemeral=True
            )
            return
        
        try:
            # Validate timezone
            pytz.timezone(timezone)
            # Validate date
            datetime(2000, month, day)
        except (ValueError, pytz.exceptions.UnknownTimeZoneError):
            await interaction.response.send_message(
                "Invalid date or timezone! Please check your input.",
                ephemeral=True
            )
            return
        
        self.birthdays[str(interaction.user.id)] = {
            "day": day,
            "month": month,
            "timezone": timezone
        }
        self.save_birthdays()
        
        await interaction.response.send_message(
            f"Birthday set to {month}/{day} ({timezone})!",
            ephemeral=True
        )

    @app_commands.command(name="birthday list", description="List all birthdays")
    async def birthday_list(self, interaction: discord.Interaction):
        if interaction.channel_id != self.birthday_channel_id:
            await interaction.response.send_message(
                "This command can only be used in the birthdays channel!",
                ephemeral=True
            )
            return
            
        if not self.birthdays:
            await interaction.response.send_message(
                "No birthdays set yet!",
                ephemeral=True
            )
            return
        
        sorted_birthdays = sorted(
            self.birthdays.items(),
            key=lambda x: (x[1]['month'], x[1]['day'])
        )
        
        pages = []
        items_per_page = 30
        
        for i in range(0, len(sorted_birthdays), items_per_page):
            page_birthdays = sorted_birthdays[i:i + items_per_page]
            
            description = "Use `/birthday set` to add your birthday!\n\n"
            for user_id, bday in page_birthdays:
                user = interaction.guild.get_member(int(user_id))
                if user:
                    description += f"{bday['month']}/{bday['day']} - {user.name}\n"
            
            embed = discord.Embed(
                title="Birthday List",
                description=description,
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Total Birthdays: {len(self.birthdays)}")
            pages.append(embed)
        
        await interaction.response.send_message(
            embed=pages[0],
            view=BirthdayPageView(pages)
        )

    async def birthday_check_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                current_time = datetime.now(pytz.UTC)
                
                for user_id, data in self.birthdays.items():
                    user_tz = pytz.timezone(data['timezone'])
                    user_time = current_time.astimezone(user_tz)
                    
                    if user_time.day == data['day'] and user_time.month == data['month']:
                        user = self.bot.get_user(int(user_id))
                        if user and str(user_id) not in self.active_birthday_roles:
                            guild = self.bot.guilds[0]
                            member = guild.get_member(int(user_id))
                            channel = self.bot.get_channel(self.birthday_channel_id)
                            
                            if member and channel:
                                role = guild.get_role(self.birthday_role_id)
                                await member.add_roles(role)
                                await channel.send(f"@everyone 🎉 Happy Birthday {user.mention}! 🎂")
                                self.active_birthday_roles[str(user_id)] = current_time.timestamp()
                                self.save_active_roles()
                
                # Check for role removals
                for user_id, timestamp in list(self.active_birthday_roles.items()):
                    if current_time.timestamp() - timestamp >= 86400:  # 24 hours
                        guild = self.bot.guilds[0]
                        member = guild.get_member(int(user_id))
                        role = guild.get_role(self.birthday_role_id)
                        
                        if member and role in member.roles:
                            await member.remove_roles(role)
                        
                        del self.active_birthday_roles[user_id]
                        self.save_active_roles()
                
            except Exception as e:
                print(f"Error in birthday check loop: {e}")
            
            await asyncio.sleep(60)  # Check every minute

async def setup(bot):
    await bot.add_cog(Birthdays(bot))
