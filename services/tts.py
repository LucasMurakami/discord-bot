import discord
from gtts import gTTS
import os
import tempfile
import asyncio
from pydub import AudioSegment
from discord import FFmpegPCMAudio
from discord.ext import commands

class TTSService():
    def __init__(self):
        self.temp_files = []

    """Generate speech audio from text and return file path."""
    async def generate_speech(self, text: str, lang: str = 'en') -> str:
        
        try:
            # Generate speech with gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_file:
                tts.save(mp3_file.name)

            # Convert to PCM format for Discord
            wav_path = mp3_file.name.replace(".mp3", ".wav")
            sound = AudioSegment.from_file(mp3_file.name, format="mp3")
            sound.export(wav_path, format="wav")

            # Store for cleanup
            self.temp_files.append(mp3_file.name)
            self.temp_files.append(wav_path)

            return wav_path
            
        except Exception as e:
            print(f"TTS Error: {str(e)}")
            return None

    
    """Clean up temporary files"""
    def cleanup(self):
        
        for file in self.temp_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
        self.temp_files = []


    """Convert text to speech and play it"""
    async def speak(self, ctx, *, text: str):
        
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel!")

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client:
            if ctx.voice_client.channel != voice_channel:
                await ctx.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        # Generate speech
        wav_path = await self.generate_speech(text)
        if not wav_path:
            return await ctx.send("❌ Failed to generate speech")

        while ctx.voice_client.is_playing():
            await asyncio.sleep(1)

        # Play audio
        source = FFmpegPCMAudio(wav_path)
        ctx.voice_client.play(
            source,
            after=lambda e: self.cleanup() if e else None
        )

        await ctx.send(f"🔊 **Speaking**: {text}")
