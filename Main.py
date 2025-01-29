import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
import os

load_dotenv()

# Required intents configuration
intents = discord.Intents.default()
intents.message_content = True  # Enable message content access

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None  # Optional: Disable default help command
)

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
}

@bot.event
async def on_ready():
    print(f'Connected as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="type !help to see all commands"))

@bot.command()
async def help(ctx):
    """Show help menu"""
    embed = discord.Embed(title="Bot Test - 3.2 - !HELP", color=0x00ff00)
    embed.add_field(name="!help", value="Show this help menu", inline=False)
    embed.add_field(name="!join", value="Join voice channel", inline=False)
    embed.add_field(name="!leave", value="Leave voice channel", inline=False)
    embed.add_field(name="!play <url>", value="Join voice channel and start playing url", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    """Joins a voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You must be in a voice channel to use this command.")

@bot.command()
async def leave(ctx):
    """Leaves the voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I am not connected to a voice channel.")

@bot.command()
async def play(ctx, url):
    """Plays audio from a YouTube URL"""
    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)

    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    
    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)

@bot.command()
async def stop(ctx):
    """Skips the current audio"""
    if ctx.voice_client:
        ctx.voice_client.stop()
    else:
        await ctx.send("I am not connected to a voice channel.")

bot.run(os.getenv('DISCORD_TOKEN'))