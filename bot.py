import logging
import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Configure logging to capture bot events and errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)
discord_logger = logging.getLogger('discord') 
discord_logger.setLevel(logging.INFO)  

# Load environment variables from .env file (e.g., bot token)
load_dotenv()

# Set bot intents (permissions needed for certain events)
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content for commands

# Initialize the bot with command prefix, intents, and presence settings
bot = commands.Bot(
    command_prefix='!', 
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions.none(),
    activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name="your commands"
    ),
    member_cache_flags=discord.MemberCacheFlags.none() 
)

@bot.event
async def on_ready():
    """Triggered when the bot successfully connects to Discord."""
    print(f'Connected as {bot.user} (ID: {bot.user.id})') 
    await bot.change_presence(activity=discord.Game(name="type !help to see all commands")) 

async def load_cogs():
    """Loads bot command cogs (separate command files)."""
    await bot.load_extension("cogs.basicCommands") 
    await bot.load_extension("cogs.music")  
    await bot.load_extension("cogs.tts")

async def main():
    """Main function to start the bot asynchronously."""
    async with bot:
        await load_cogs() 
        await bot.start(os.getenv('DISCORD_TOKEN')) 

# Run the bot if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main())  # Launch the bot event loop
