import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from utils.yt_helper import YTDLHelper

# CONSTS

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn -acodec libopus -b:a 128k -f opus'
}

valid_formats = (
    'webm', 'opus', 'm4a',
    'mp3', 'ogg', 'wav',
    'aac', 'flac'
)

class Song:
    def __init__(self, url, title, requester):
        """
        Initializes a song object.

        Args:
            url (str): The direct audio URL of the song.
            title (str): The title of the song.
            requester (str): The name of the user who requested the song.
        """
        self.url = url
        self.title = title
        self.requester = requester
        
    def copy(self):
        """Returns a copy of the song object."""
        return Song(self.url, self.title, self.requester)


class GuildMusicState:
    def __init__(self):
        """
        Initializes the music state for a Discord guild.

        Attributes:
            queue (list): A list of songs waiting to be played.
            current (Song | None): The currently playing song.
            voice_client (discord.VoiceClient | None): The voice connection for the guild.
            repeat_mode (str): The repeat mode setting ('off' or 'on').
            repeat_song (Song | None): The song to repeat when repeat mode is enabled.
            original_playlist (list): Stores the original order of songs in case shuffle or repeat is applied.
        """
        self.queue = []
        self.current = None
        self.voice_client = None
        self.repeat_mode = 'off'  # 'off', 'on'
        self.repeat_song = None
        self.original_playlist = []

    def cleanup(self):
        """
        Stops playback, clears the queue, and disconnects the bot when no more songs are available.

        This method is called when the queue is empty or an error occurs during playback.
        """
        self.queue.clear()
        self.current = None
        self.repeat_song = None
        if self.voice_client:
            asyncio.run_coroutine_threadsafe(self.voice_client.disconnect(), self.voice_client.loop)
            self.voice_client = None

    def check_queue(self, ctx, error):
        """
        Handles playback continuation when a song finishes or encounters an error.

        Args:
            ctx (commands.Context): The context of the command.
            error (Exception | None): The error encountered during playback, if any.
        """
        if error:
            print(f"Playback error: {error}")
            self.cleanup()
            return

        try:
            if self.repeat_mode == 'on' and self.repeat_song:
                # If repeat mode is on, replay the same song
                self.current = self.repeat_song.copy()
                source = discord.FFmpegOpusAudio(self.current.url, **ffmpeg_options)
                
                async def send_and_delete():
                    msg = await ctx.send(f"🎶 Now playing: {self.current.title} (on repeat)")
                
                asyncio.run_coroutine_threadsafe(send_and_delete(), ctx.bot.loop)
                self.voice_client.play(source, after=lambda e: self.check_queue(ctx, e))
            else:
                if self.queue:
                    # Play the next song in queue
                    self.current = self.queue.pop(0)
                    source = discord.FFmpegOpusAudio(self.current.url, **ffmpeg_options)
                    
                    async def send_and_delete():
                        msg = await ctx.send(f"🎶 Now playing: {self.current.title}")
                    
                    asyncio.run_coroutine_threadsafe(send_and_delete(), ctx.bot.loop)
                    self.voice_client.play(source, after=lambda e: self.check_queue(ctx, e))
                else:
                    self.cleanup()
        except Exception as e:
            print(f"Playback failed: {e}")
            self.cleanup()


class Music(commands.Cog):
    def __init__(self, bot):
        """
        Initializes the music cog.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot
        self.guild_states = {}

    def get_guild_state(self, guild_id):
        """
        Retrieves the music state for a guild, creating one if it doesn't exist.

        Args:
            guild_id (int): The ID of the Discord guild.

        Returns:
            GuildMusicState: The music state object for the guild.
        """
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildMusicState()
        return self.guild_states[guild_id]

    @commands.command()
    async def play(self, ctx, *, url):
        """
        Plays a song from the given URL or adds it to the queue if a song is already playing.

        Args:
            ctx (commands.Context): The command context.
            url (str): The URL of the song to play.

        If a song is already playing, the new song is added to the queue.
        """
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command!")

        guild_state = self.get_guild_state(ctx.guild.id)
        if not guild_state.voice_client:
            guild_state.voice_client = await ctx.author.voice.channel.connect()
        elif guild_state.voice_client.channel != ctx.author.voice.channel:
            await guild_state.voice_client.move_to(ctx.author.voice.channel)

        msg = await ctx.send("⏳ Processing...")
        info = await YTDLHelper.extract_info(url)

        if not info:
            return await msg.edit(content="❌ Could not retrieve song information or it's a playlist.")

        # Process the song entry - either a single song or a playlist (playlist won't be supported in this version)
        if '_type' in info and info['_type'] == 'playlist':
            entries = info['entries']
        else:
            entries = [info]

        added_songs = 0
        for entry in entries:
            if not entry:
                continue
                
            format = next(
                (f for f in entry.get('formats', []) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'),
                None
            )
            
            if not format:
                continue

            if not any(fmt in format['url'] for fmt in valid_formats):
                continue  

            song = Song(url=format['url'], title=entry.get('title', 'Unknown Title'), requester=ctx.author.display_name)
            guild_state.queue.append(song)
            added_songs += 1

        if added_songs == 0:
            return await msg.edit(content="❌ No playable audio found")

        if not guild_state.voice_client.is_playing():
            guild_state.check_queue(ctx, None)
            await msg.delete()
        else:
            await msg.edit(content=f"✅ Added {added_songs} songs to queue")

    @commands.command()
    async def skip(self, ctx):
        """Skips the currently playing song."""
        guild_state = self.get_guild_state(ctx.guild.id)
        if guild_state.voice_client:
            guild_state.voice_client.stop()
            await ctx.send("⏭ Skipped current song")

    @commands.command()
    async def queue(self, ctx):
        """Displays the current queue of songs."""
        guild_state = self.get_guild_state(ctx.guild.id)
        embed = discord.Embed(title="Music Queue", color=0x00ff00)

        if guild_state.current:
            embed.add_field(name="Now Playing", value=f"**{guild_state.current.title}** (requested by {guild_state.current.requester})", inline=False)

        if guild_state.queue:
            queue_list = "\n".join([f"{i+1}. {song.title} (requested by {song.requester})" for i, song in enumerate(guild_state.queue[:10])])
            embed.add_field(name=f"Upcoming Songs ({len(guild_state.queue)} total)", value=queue_list, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Registers the music cog with the bot."""
    await bot.add_cog(Music(bot))
