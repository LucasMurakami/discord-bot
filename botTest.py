import discord
import os
import asyncio
import torch
import whisper
import numpy as np
from collections import defaultdict
from discord.ext import commands, voice_recv
from dotenv import load_dotenv

load_dotenv(".env")
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=device)

class StreamAudioSink(voice_recv.AudioSink):
    def __init__(self, text_channel):
        self.text_channel = text_channel
        self.audio_buffers = defaultdict(bytes)
        self.sample_rate = 48000  # Discord's input sample rate
        self.target_rate = 16000  # Whisper's required sample rate
        self.buffer_duration = 5  # Process every 5 seconds of audio
        self.processing = False

    def wants_opus(self):
        return False  # We want raw PCM samples

    def write(self, user, data):
        """Collect raw PCM audio data from users"""
        if data:
            self.audio_buffers[user.id] += data.pcm

    async def process_audio(self):
        """Process audio buffers at regular intervals"""
        while self.processing:
            await asyncio.sleep(self.buffer_duration)
            await self._process_buffers()

    async def _process_buffers(self):
        """Convert and transcribe collected audio"""
        for user_id, buffer in self.audio_buffers.items():
            if len(buffer) == 0:
                continue

            try:
                # Convert raw bytes to numpy array (optimized)
                audio_array = np.frombuffer(buffer, np.int16)
                audio_array = audio_array.astype(np.float32) / 32768.0
                
                
                # Resample to Whisper's required format
                audio_resampled = self._resample_audio(audio_array)
                
                # Transcribe using Whisper
                result = await asyncio.to_thread(
                    model.transcribe,
                    audio_resampled,
                    language='pt',
                    fp16=False
                )
                
                # Send transcription to text channel
                user = await bot.fetch_user(user_id)
                await self.text_channel.send(f"{user.display_name}: {result['text']}")

            except Exception as e:
                print(f"Processing error: {str(e)}")
            finally:
                # Clear processed audio from buffer
                self.audio_buffers[user_id] = b''

    def _resample_audio(self, audio):
        """Resample audio from 48kHz to 16kHz and convert to mono"""
        # Convert stereo to mono by averaging channels
        mono_audio = audio.reshape(-1, 2).mean(axis=1)
            
        # Resample from 48kHz to 16kHz
        ratio = self.target_rate / self.sample_rate
        n_samples = int(np.round(len(mono_audio) * ratio))
        resampled = np.interp(
            np.linspace(0, len(mono_audio), n_samples),
            np.arange(len(mono_audio)),
            mono_audio
        )
        return resampled.astype(np.float32)  # Add explicit type conversion here

    async def start_processing(self):
        """Start the processing loop"""
        self.processing = True
        asyncio.create_task(self.process_audio())

    def cleanup(self):
        """Stop processing and clear buffers"""
        self.processing = False
        self.audio_buffers.clear()

@bot.command()
async def join(ctx):
    """Join voice channel and start live transcription"""
    if not ctx.author.voice:
        return await ctx.send("You need to be in a voice channel!")

    try:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

        vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
        sink = StreamAudioSink(ctx.channel)
        vc.listen(sink)
        await sink.start_processing()
        await ctx.send(f"Joined {channel} and started live transcription!")

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
async def leave(ctx):
    """Leave voice channel and stop transcription"""
    if ctx.voice_client:
        if hasattr(ctx.voice_client, 'listener'):
            ctx.voice_client.listener.cleanup()
        await ctx.voice_client.disconnect()
        await ctx.send("Left voice channel and stopped transcription.")
    else:
        await ctx.send("Not currently in a voice channel!")

bot.run(BOT_TOKEN)