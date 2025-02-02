import discord
import os
import time
import asyncio
import numpy as np
from collections import defaultdict
from discord.ext import commands, voice_recv
from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer
from scipy.signal import resample_poly
import json
import logging

# Configure logging (set level to DEBUG to see debug messages)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv(".env")
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

model = Model("model/vosk-model-small-pt-0.3")

class StreamAudioSink(voice_recv.AudioSink):
    def __init__(self, text_channel):
        self.text_channel = text_channel
        self.audio_buffers = defaultdict(bytes)
        self.sample_rate = 48000
        self.target_rate = 16000
        self.active = True
        self.recognizers = {}
        self.last_partials = {}
        self.last_audio_time = {}  # Track the last time we received audio per user
        self.lock = asyncio.Lock()
        self.processing_task = asyncio.create_task(self.process_audio())

    def wants_opus(self):
        return False

    def write(self, user, data):
        if self.active and data and data.pcm:
            self.audio_buffers[user.id] += data.pcm
            # Update last audio timestamp for this user
            self.last_audio_time[user.id] = time.time()
            logging.debug(f"Received audio from user {user.id} (buffer size: {len(self.audio_buffers[user.id])} bytes)")

    async def process_audio(self):
        while self.active:
            # Process more frequently if needed (e.g., every 0.2s)
            await asyncio.sleep(0.5)
            async with self.lock:
                await self._process_buffers()

    async def _process_buffers(self):
        now = time.time()
        for user_id in list(self.audio_buffers.keys()):
            buffer = self.audio_buffers[user_id]
            # Check silence: if no audio received for at least 1 second and buffer is non-empty
            last_time = self.last_audio_time.get(user_id, now)
            silence_duration = now - last_time
            if silence_duration >= 1 and buffer:
                logging.debug(f"Silence detected for user {user_id} ({silence_duration:.2f}s); finalizing utterance")
                if user_id not in self.recognizers:
                    self.recognizers[user_id] = KaldiRecognizer(model, self.target_rate)
                    self.recognizers[user_id].SetWords(False)
                recognizer = self.recognizers[user_id]
                # Force final result on silence
                final_json = recognizer.FinalResult()
                final_result = json.loads(final_json)
                text = final_result.get("text", "")
                if text:
                    await self.send_transcription(user_id, text)
                # Reset the recognizer and clear the buffer
                self.recognizers[user_id] = KaldiRecognizer(model, self.target_rate)
                self.recognizers[user_id].SetWords(False)
                self.audio_buffers[user_id] = b""
                self.last_partials.pop(user_id, None)
                continue  # Move to next user

            # Otherwise, process only if there's enough audio (e.g., 200ms worth)
            if len(buffer) < 9600:
                continue

            try:
                logging.debug(f"Processing buffer for user {user_id} (size: {len(buffer)} bytes)")
                audio_array = np.frombuffer(buffer, dtype=np.int16)
                resampled = self.resample_audio(audio_array)
                if resampled.size == 0:
                    continue

                if user_id not in self.recognizers:
                    self.recognizers[user_id] = KaldiRecognizer(model, self.target_rate)
                    self.recognizers[user_id].SetWords(False)
                    logging.debug(f"Created new recognizer for user {user_id}")

                recognizer = self.recognizers[user_id]
                
                # Feed audio to the recognizer
                if recognizer.AcceptWaveform(resampled.tobytes()):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    logging.debug(f"Final result for user {user_id}: {result}")
                    if text:
                        await self.send_transcription(user_id, text)
                        self.last_partials.pop(user_id, None)
                    # Clear the buffer after a final result
                    self.audio_buffers[user_id] = b""
                else:
                    partial_result = json.loads(recognizer.PartialResult())
                    partial = partial_result.get("partial", "")
                    logging.debug(f"Partial result for user {user_id}: {partial_result}")
                    if partial and partial != self.last_partials.get(user_id):
                        await self.send_transcription(user_id, partial, is_partial=True)
                        self.last_partials[user_id] = partial
                    # Retain a short overlap to avoid cutting off words
                    self.audio_buffers[user_id] = buffer[-int(0.1 * self.sample_rate * 2):]
            except Exception as e:
                logging.error(f"Processing error for user {user_id}: {str(e)}")
                self.cleanup_user(user_id)

    def resample_audio(self, audio):
        """Resample audio using proper polyphase resampling"""
        if len(audio) == 0:
            return np.array([], dtype=np.int16)
        
        # Stereo to mono conversion
        if len(audio) % 2 != 0:
            audio = audio[:-1]
        mono_audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
        
        # Calculate resampling ratio (48kHz -> 16kHz = 1:3)
        resampled = resample_poly(mono_audio, 1, 3).astype(np.int16)
        logging.debug(f"Resampled audio length: {len(resampled)} samples")
        return resampled

    async def send_transcription(self, user_id, text, is_partial=False):
        try:
            user = await bot.fetch_user(user_id)
            mode = "Partial" if is_partial else "Final"
            message = f"**{user.display_name}:** {text}"
            logging.debug(f"Sending {mode} transcription for user {user_id}: {text}")
            await self.text_channel.send(message)
        except Exception as e:
            logging.error(f"Send message error for user {user_id}: {str(e)}")

    def cleanup_user(self, user_id):
        self.audio_buffers.pop(user_id, None)
        self.last_partials.pop(user_id, None)
        self.last_audio_time.pop(user_id, None)
        if user_id in self.recognizers:
            del self.recognizers[user_id]

    def cleanup(self):
        self.active = False
        self.audio_buffers.clear()
        self.recognizers.clear()
        self.last_partials.clear()
        self.last_audio_time.clear()
        if self.processing_task:
            self.processing_task.cancel()

@bot.command()
async def join(ctx):
    try:
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel!")

        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

        vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
        sink = StreamAudioSink(ctx.channel)
        vc.listen(sink)
        await ctx.send(f"Connected to {channel.name} - Transcription active!")
    except Exception as e:
        logging.error(f"Join error: {str(e)}")
        await ctx.send(f"Error: {str(e)}")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

@bot.command()
async def sair(ctx):
    if ctx.voice_client:
        if hasattr(ctx.voice_client, 'listener'):
            ctx.voice_client.listener.cleanup()
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from voice channel.")
    else:
        await ctx.send("Not in a voice channel!")

@bot.event
async def on_ready():
    logging.info(f'Bot connected as {bot.user}')

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
