import discord
from discord.ext import commands

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """Bot joins the user's voice channel."""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("You must be in a voice channel to use this command.")

    @commands.command()
    async def leave(self, ctx):
        """Bot leaves the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Left voice channel")
        else:
            await ctx.send("I'm not connected to a voice channel.")
    
    @commands.command()
    async def help(self, ctx):
        """Bot shows the help menu."""
        embed = discord.Embed(title="Bot Commands", color=0x00ff00)
        embed.add_field(name="!help", value="Show this help menu", inline=False)
        embed.add_field(name="!join", value="Join your voice channel", inline=False)
        embed.add_field(name="!leave", value="Leave voice channel", inline=False)
        embed.add_field(name="!play <url/search>", value="Play music or add to queue (currently this version doesn't support playlists.)", inline=False)
        embed.add_field(name="!skip", value="Skip current song", inline=False)
        embed.add_field(name="!queue", value="Show current queue", inline=False)
        embed.add_field(name="!repeat", value="Repeat the current song (off by default) - it ignores the queue and loops the current music when the command is executed.", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BasicCommands(bot))
