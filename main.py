import discord
from discord.commands import Option
from discord.ext import commands
import os
from dotenv import load_dotenv
from moderation import setup_moderation
from filter import setup_filter
from logs import setup_logs

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="/help for commands"))

@bot.slash_command(name="ping", description="Check the bot's latency")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="Pong! 🏓", description=f"Latency: {latency}ms", color=discord.Color.green())
    await ctx.respond(embed=embed)

def setup(bot):
    setup_moderation(bot)
    setup_filter(bot)
    setup_logs(bot)

setup(bot)

bot.run(os.getenv('TOKEN'))