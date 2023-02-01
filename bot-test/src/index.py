import youtube_dl
import asyncio
import discord
import random
import time
import os
from discord.ext import commands

youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Elegir el primer item de la lista
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Dj Calorias"), status=discord.Status.idle)
    print('bot ready')


@bot.command(description="joins a voice channel")
async def join(ctx):
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        return await ctx.send('No seas mogolico y metete a un canal de voz antes!')

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)
        vc = ctx.voice_client


async def on_ready(self):
    for guild in self.client.guilds:
        self.song_queue[guild.id] = []


async def check_queue(ctx):
    if len(ctx.song_queue[ctx.guild.id]) > 0:
        ctx.voice_client.stop()
        await ctx.play(ctx.song_queue[ctx.guild.id][0])


@bot.command(description="streams music", aliases=['pl', 'p'])
async def play(ctx, *, url):
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e)
                              if e else None)
        await ctx.send('sonando: **{}**'.format(player.title))
        song_queue = check_queue(ctx)
        song_queue[ctx.guild.id].append(player)


@bot.command(description="stops and disconnects the bot from voice")
async def stop(ctx):
    await ctx.voice_client.disconnect()
    await ctx.send('Ya pare')


@play.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("No seas mogolico y metete a un canal de voz antes!")
            raise commands.CommandError(
                "Si que sos trolo")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()


bot.run('MTA1OTAwNjIyMjM0MDE5NDQyNg.GqYuAh.qfDNT9CKkc1585wKX2qmGJC3hQYdLxSDyB4RJs')
