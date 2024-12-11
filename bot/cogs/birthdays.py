import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime
import pytz
import asyncio
import time

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
        self.guild_id = 1176076930647453696
        self.active_birthday_roles = self.load_active_roles()
        self.command_cooldowns = {}
        self.role_update_queue = asyncio.Queue()
        self.bot.loop.create_task(self.birthday_check_loop())
        self.bot.loop.create_task(self.process_role_updates())
    
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

    async def process_role_updates(self):
        while True:
            try:
                update = await self.role_update_queue.get()
                member, role, add = update
                
                if add:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
                    
                await asyncio.sleep(1)  # Rate limit prevention
            except Exception as e:
                print(f"Role update error: {e}")
                await asyncio.sleep(5)

    @app_commands.command(name="birthdayset", description="Set your birthday")
    @app_commands.describe(
        day="Day of your birthday (1-31)",
        month="Month of your birthday (1-12)",
        timezone="Your timezone (Example: UTC+10, America/New_York)"
    )
    async def birthday_set(
        self,
        interaction: discord.Interaction,
        day: int,
        month: int,
        timezone: str
    ):
        user_id = str(interaction.user.id)
        current_time = time.time()
        
        if user_id in self.command_cooldowns:
            if current_time - self.command_cooldowns[user_id] < 60:  # 1 minute cooldown
                await interaction.response.send_message("Please wait before using this command again.", ephemeral=True)
                return
                
        self.command_cooldowns[user_id] = current_time

        if interaction.channel_id != self.birthday_channel_id:
            await interaction.response.send_message("This command can only be used in the birthdays channel!", ephemeral=True)
            return
            
        try:
            pytz.timezone(timezone)
            datetime(2000, month, day)
        except (ValueError, pytz.exceptions.UnknownTimeZoneError):
            await interaction.response.send_message("Invalid date or timezone! Please check your input.", ephemeral=True)
            return
        
        self.birthdays[user_id] = {
            "day": day,
            "month": month,
            "timezone": timezone
        }
        self.save_birthdays()
        
        await interaction.response.send_message(f"Birthday set to {month}/{day} ({timezone})!", ephemeral=True)

    @app_commands.command(name="birthdaylist", description="List all birthdays")
    async def birthday_list(self, interaction: discord.Interaction):
        if 'birthdaylist' in self.command_cooldowns:
            if time.time() - self.command_cooldowns['birthdaylist'] < 30:  # 30 second global cooldown
                await interaction.response.send_message("This command is on cooldown.", ephemeral=True)
                return
        
        self.command_cooldowns['birthdaylist'] = time.time()

        if interaction.channel_id != self.birthday_channel_id:
            await interaction.response.send_message("This command can only be used in the birthdays channel!", ephemeral=True)
            return
            
        if not self.birthdays:
            await interaction.response.send_message("No birthdays set yet!", ephemeral=True)
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Could not find server!", ephemeral=True)
            return
            
        sorted_birthdays = sorted(
            self.birthdays.items(),
            key=lambda x: (x[1]['month'], x[1]['day'])
        )
        
        pages = []
        items_per_page = 30
        
        for i in range(0, len(sorted_birthdays), items_per_page):
            page_birthdays = sorted_birthdays[i:i + items_per_page]
            
            description = "Use `/birthdayset` to add your birthday!\n\n"
            for user_id, bday in page_birthdays:
                user = guild.get_member(int(user_id))
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
                                await self.role_update_queue.put((member, role, True))
                                await channel.send(f"@everyone 🎉 Happy Birthday {member.mention}! 🎂")
                                self.active_birthday_roles[str(user_id)] = current_time.timestamp()
                                self.save_active_roles()
                
                for user_id, timestamp in list(self.active_birthday_roles.items()):
                    if current_time.timestamp() - timestamp >= 86400:  # 24 hours
                        member = guild.get_member(int(user_id))
                        role = guild.get_role(self.birthday_role_id)
                        
                        if member and role in member.roles:
                            await self.role_update_queue.put((member, role, False))
                        
                        del self.active_birthday_roles[user_id]
                        self.save_active_roles()
                
            except Exception as e:
                print(f"Error in birthday check loop: {e}")
            
            await asyncio.sleep(60)

async def setup(bot):
    await bot.add_cog(Birthdays(bot))
