import os
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio

class Assistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Ask the assistant a question and get a spoken response."""
    @commands.command(name='ask')
    async def ask_voice(self, ctx, *, prompt):        
        # Check if user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel!")
            return

        # Connect to voice channel
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if not voice_client or not voice_client.is_connected():
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        # Access Ollama cog for AI response
        ollama_service = self.bot.ollama
        if not ollama_service:
            await ctx.send("Ollama service is unavailable.")
            return

        # Generate AI response
        async with ctx.typing():
            response_text = await ollama_service.generate_text_voice_response(prompt)

        if not response_text or "Error" in response_text:
            await ctx.send("❌ Failed to generate response.")
            return

        # Access TTS cog for speech generation
        tts_service = self.bot.tts
        if not tts_service:
            await ctx.send("TTS service is unavailable.")
            return

        async with ctx.typing():
            await tts_service.speak(ctx, text=response_text)


    """Ask the assistant a question and get a text response."""
    @commands.command(name='ask_text')
    async def ask_text(self, ctx, *, prompt: str):
       
        ollama_service = self.bot.ollama

        if not ollama_service:
            await ctx.send("Ollama service is unavailable.")
            return
        
        async with ctx.typing():
            response_text = await ollama_service.generate_text_response(prompt)

        await ctx.send(f"🔊 **Speaking:** {response_text}")

"""Registers the assistant cog with the bot."""
async def setup(bot):
    await bot.add_cog(Assistant(bot))
