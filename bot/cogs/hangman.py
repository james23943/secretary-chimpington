import discord
from discord.ext import commands
import random

class HangmanGame:
    def __init__(self, word):
        self.word = word
        self.guesses = set()
        self.attempts = 6
        self.participants = set()

    def guess(self, letter, user_id):
        if letter in self.guesses:
            return False, "Already guessed"
        self.guesses.add(letter)
        self.participants.add(user_id)
        if letter not in self.word:
            self.attempts -= 1
        return True, self.get_display_word()

    def get_display_word(self):
        return ''.join(c if c in self.guesses else '_' for c in self.word)

    def is_won(self):
        return all(c in self.guesses for c in self.word)

    def is_lost(self):
        return self.attempts <= 0

class HangmanView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=120)
        self.game = game
        self.create_buttons()

    def create_buttons(self):
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            self.add_item(HangmanButton(letter, self))

class HangmanButton(discord.ui.Button):
    def __init__(self, letter, view):
        super().__init__(label=letter, style=discord.ButtonStyle.primary)
        self.letter = letter
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        game = self.view.game
        valid, result = game.guess(self.letter, interaction.user.id)
        if not valid:
            await interaction.response.send_message(result, ephemeral=True)
            return

        if game.is_won():
            await interaction.response.edit_message(content=f"Congratulations! The word was: {game.word}. Participants: {', '.join(str(user) for user in game.participants)}", view=None)
            self.view.stop()
        elif game.is_lost():
            await interaction.response.edit_message(content=f"Game over! The word was '{game.word}'. Participants: {', '.join(str(user) for user in game.participants)}", view=None)
            self.view.stop()
        else:
            display_word = game.get_display_word()
            await interaction.response.edit_message(content=f"Word: {display_word} | Attempts left: {game.attempts}")

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_game = None

    @commands.command(name='hangmanstart')
    async def start_game(self, ctx):
        """Start a new game of Hangman."""
        if self.active_game:
            await ctx.send("A game is already in progress!")
            return

        word_list = ['python', 'discord', 'hangman', 'bot', 'cog']
        word = random.choice(word_list)
        self.active_game = HangmanGame(word)

        view = HangmanView(self.active_game)
        await ctx.send(f"A new game of Hangman has started! Word: {self.active_game.get_display_word()} | Attempts left: {self.active_game.attempts}", view=view)

async def setup(bot):
    await bot.add_cog(Hangman(bot))
