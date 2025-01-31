import logging
import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from services.ollama import OllamaService
from services.tts import TTSService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)
discord_logger = logging.getLogger('discord') 
discord_logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv('.env')
BOT_TOKEN = os.getenv('DISCORD_TOKEN')

# Validate environment variables
REQUIRED_ENV = ['DISCORD_TOKEN', 'OLLAMA_URL', 'OLLAMA_MODEL']
for var in REQUIRED_ENV:
    if not os.getenv(var):
        raise RuntimeError(f"Missing required environment variable: {var}")

# Set bot intents
intents = discord.Intents.default()
intents.message_content = True

"""Custom bot class to handle events and commands"""	
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
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
        self.ollama = OllamaService()
        self.tts = TTSService()

    """Called when the bot is fully connected"""
    async def on_ready(self):        
        print(f'Connected as {self.user} (ID: {self.user.id})')
        await self.change_presence(
            activity=discord.Game(name="type !help for commands")
        )


"""Load all command cogs"""
async def load_cogs(bot: Bot):
    
    cogs = [
        "cogs.basicCommands",
        "cogs.music",
        "cogs.assistant"
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logging.info(f"Successfully loaded cog: {cog}")
        except Exception as e:
            logging.error(f"Failed to load cog {cog}: {str(e)}")


"""Main function to start the bot"""
async def main():
    bot = Bot()
    async with bot:
        await load_cogs(bot)
        await bot.start(BOT_TOKEN)
    await bot.ollama.close()
    await bot.tts.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shutdown requested")