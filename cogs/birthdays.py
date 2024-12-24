import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime
import pytz
import asyncio
from pathlib import Path
from typing import Dict

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
    def __init__(self, bot, config):
        self.bot = bot
        self.birthdays_path = Path(__file__).parent.parent / 'data' / 'birthdays.json'
        self.active_roles_path = Path(__file__).parent.parent / 'data' / 'active_birthday_roles.json'
        self.birthdays = self.load_birthdays()
        self.birthday_role_id = config['birthday_role_id']
        self.birthday_channel_id = config['birthday_channel_id']
        self.guild_id = config['guild_id']
        self.active_birthday_roles = self.load_active_roles()
        self.command_cooldowns: Dict[int, float] = {}
        self.COMMAND_COOLDOWN = 5.0
        self.bot.loop.create_task(self.birthday_check_loop())
    
    def load_birthdays(self):
        try:
            with open(self.birthdays_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_birthdays(self):
        with open(self.birthdays_path, 'w') as f:
            json.dump(self.birthdays, f)
    
    def load_active_roles(self):
        try:
            with open(self.active_roles_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_active_roles(self):
        with open(self.active_roles_path, 'w') as f:
            json.dump(self.active_birthday_roles, f)

    @app_commands.command(name="birthday", description="Set or list birthdays")
    @app_commands.choices(action=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="list", value="list")
    ])
    async def birthday(
        self, 
        interaction: discord.Interaction, 
        action: str,
        day: int = None,
        month: int = None,
        timezone: str = None
    ):
        current_time = discord.utils.utcnow().timestamp()
        user_id = interaction.user.id

        if interaction.channel_id != self.birthday_channel_id:
            await interaction.response.send_message(
                "This command can only be used in the birthdays channel!",
                ephemeral=True
            )
            return

        if user_id in self.command_cooldowns:
            remaining = self.COMMAND_COOLDOWN - (current_time - self.command_cooldowns[user_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"Command available in {remaining:.1f} seconds.",
                    ephemeral=True
                )
                return

        self.command_cooldowns[user_id] = current_time

        if action == "set":
            if not all([day, month, timezone]):
                await interaction.response.send_message(
                    "Please provide day, month, and timezone.",
                    ephemeral=True
                )
                return
                
            try:
                pytz.timezone(timezone)
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
            
        elif action == "list":
            await self.send_birthday_list(interaction)

    async def send_birthday_list(self, interaction: discord.Interaction):
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
                    month_name = datetime(2000, bday['month'], 1).strftime('%B')
                    safe_name = discord.utils.escape_markdown(user.name)
                    description += f"**{month_name} {bday['day']}**: {safe_name}\n\n"
            
            embed = discord.Embed(
                title="Birthday List 🎂",
                description=description,
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"🎉 Page {i//items_per_page + 1}/{len(range(0, len(sorted_birthdays), items_per_page))} • Showing {len(page_birthdays)} birthdays • Total: {len(self.birthdays)}")
            pages.append(embed)
        
        if pages:
            await interaction.response.send_message(
                embed=pages[0],
                view=BirthdayPageView(pages) if len(pages) > 1 else None
            )

    async def birthday_check_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                current_time = datetime.now(pytz.UTC)
                guild = self.bot.get_guild(self.guild_id)
                
                for user_id, data in self.birthdays.items():
                    user_tz = pytz.timezone(data['timezone'])
                    user_time = current_time.astimezone(user_tz)
                    
                    if user_time.day == data['day'] and user_time.month == data['month']:
                        if str(user_id) not in self.active_birthday_roles:
                            member = guild.get_member(int(user_id))
                            channel = self.bot.get_channel(self.birthday_channel_id)
                            
                            if member and channel:
                                role = guild.get_role(self.birthday_role_id)
                                try:
                                    await member.add_roles(role)
                                    await channel.send(f"@everyone 🎉 Happy Birthday {member.mention}! 🎂")
                                    self.active_birthday_roles[str(user_id)] = current_time.timestamp()
                                    self.save_active_roles()
                                except discord.HTTPException:
                                    await asyncio.sleep(1)
                
                for user_id, timestamp in list(self.active_birthday_roles.items()):
                    if current_time.timestamp() - timestamp >= 86400:
                        member = guild.get_member(int(user_id))
                        role = guild.get_role(self.birthday_role_id)
                        
                        if member and role in member.roles:
                            try:
                                await member.remove_roles(role)
                            except discord.HTTPException:
                                await asyncio.sleep(1)
                            
                        del self.active_birthday_roles[user_id]
                        self.save_active_roles()
                
            except Exception as e:
                print(f"Error in birthday check loop: {e}")
            
            await asyncio.sleep(60)

async def setup(bot):
    config = bot.config
    await bot.add_cog(Birthdays(bot, config))
