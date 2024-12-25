import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path
import asyncio
from typing import Dict

class MessageSender(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.owner_id = config['owner_id']
        self.base_path = Path(__file__).parent.parent / 'messages'
        self.cooldowns: Dict[int, float] = {}
        self.COOLDOWN_DURATION = 5.0

    @app_commands.command(name="messagesend", description="Send a predefined message")
    @app_commands.describe(
        filename="The name of the JSON file containing the message to send (without .json extension)"
    )
    async def message_send(self, interaction: discord.Interaction, filename: str):
        current_time = discord.utils.utcnow().timestamp()
        
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Not authorized.", ephemeral=True)
            return
            
        if interaction.channel_id in self.cooldowns:
            remaining = self.COOLDOWN_DURATION - (current_time - self.cooldowns[interaction.channel_id])
            if remaining > 0:
                await interaction.response.send_message(
                    f"Message sending will be available in {remaining:.1f} seconds.", 
                    ephemeral=True
                )
                return

        try:
            file_path = self.base_path / f"{filename}.json"
            with open(file_path, 'r') as f:
                message_data = json.load(f)
            
            if 'embeds' in message_data:
                message_data['embeds'] = [discord.Embed.from_dict(e) for e in message_data['embeds']]

            await interaction.response.defer(ephemeral=True)
            await asyncio.sleep(0.5) 
            
            await interaction.channel.send(**message_data)
            self.cooldowns[interaction.channel_id] = current_time
            
            await interaction.followup.send("Message sent!", ephemeral=True)
            
        except FileNotFoundError:
            await interaction.response.send_message(f"File not found: {filename}.json", ephemeral=True)
        except discord.HTTPException as e:
            await asyncio.sleep(1) 
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

async def setup(bot):
    config = bot.config
    await bot.add_cog(MessageSender(bot, config))