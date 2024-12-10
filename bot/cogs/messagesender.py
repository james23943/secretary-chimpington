import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path

class MessageSender(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 238959894168862721
        self.base_path = Path(__file__).parent.parent / 'messages'

    @app_commands.command(name="messagesend", description="Send a predefined message")
    async def message_send(self, interaction: discord.Interaction, type: str, filename: str):
        if interaction.user.id != self.owner_id:  # owner_id is set to 238959894168862721 in __init__
            await interaction.response.send_message("Not authorized.", ephemeral=True)
            return
        try:
            file_path = self.base_path / type / f"{filename}.json"
            with open(file_path, 'r') as f:
                message_data = json.load(f)

            await interaction.channel.send(**message_data)
            await interaction.response.send_message("Message sent!", ephemeral=True)
            
        except FileNotFoundError:
            await interaction.response.send_message(f"File not found: {type}/{filename}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MessageSender(bot))
