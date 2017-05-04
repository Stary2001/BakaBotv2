from command import command, CommandFlags
from plugin import Plugin
import discord
import asyncio
import datetime
import youtube_dl
import concurrent.futures
import functools
import collections
from util import pretty_time

class DJPlugin(Plugin):
    commands = {}

    def __init__(self, bot):
        super().__init__(bot)
        if bot.type != 'discord':
            return
        self.bot = bot

        self.playlist = collections.deque()
        self.playlist_coro = asyncio.get_event_loop().create_task(self.do_playlist())
        self.playlist_pull_event = asyncio.Event()
        self.announce_channel = None
        self.volume = 1.0

        # todo: centralised executor.
        self.thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def exit(self):
        self.playlist_coro.cancel()

    async def do_playlist(self):
        while True:
            await self.playlist_pull_event.wait()
            item = self.playlist.popleft()

            if len(self.playlist) == 0:
                self.playlist_pull_event.clear()

            if self.bot.discord_voice:
                if item[0] == 'yt':
                    playing_event = asyncio.Event()
                    item = item[1]

                    player = self.bot.discord_voice.create_ffmpeg_player(item['url'], after=lambda: playing_event.set())
                    self.bot.current_voice_stream = player
                    player.start()
                    player.volume = self.volume

                    duration = pretty_time(item.get('duration'))

                    self.bot.send_message(self.announce_channel, 'Now playing: {} ({})'.format(item.get('title'), duration))
                    await playing_event.wait()

    @command(commands, 'join_voice', is_async = True)
    async def command_join_voice(ctx, name):
        channel = discord.utils.find(lambda c: c.name == name and c.type == discord.ChannelType.voice, ctx.target.server.channels)
        if not channel:
            return

        if ctx.bot.discord_voice:
            await ctx.bot.discord_voice.move_to(channel)
        else:
            ctx.bot.discord_voice = await ctx.bot.discord.join_voice_channel(channel)
    
    @command(commands, 'playlist', flags=[CommandFlags.PLUGIN])
    def command_playlist(self, ctx):
        if len(self.playlist) != 0:
            ctx.reply("\n".join(map(lambda a: "{} ({})".format(a[1].get('title'), pretty_time(a[1].get('duration'))), self.playlist)))
        else:
            ctx.reply("The playlist is empty!")

    def do_ytdl(self, url):
        ydl_opts = {'format': 'webm[abr>0]/bestaudio/best'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                for i in info['entries']:
                    self.playlist.append(('yt', i))
            else:
                self.playlist.append(('yt', info))

        self.playlist_pull_event.set()

    @command(commands, 'add', is_async = True, flags=[CommandFlags.PLUGIN])
    async def command_add(self, ctx, url):
        self.announce_channel = ctx.target
        await ctx.bot.loop.run_in_executor(self.thread_executor, functools.partial(self.do_ytdl, url))

    @command(commands, 'pause')
    def command_pause(ctx):
        ctx.bot.current_voice_stream.pause()

    @command(commands, 'resume')
    def command_pause(ctx):
        ctx.bot.current_voice_stream.resume()

    @command(commands, 'next')
    def command_next(ctx):
        ctx.bot.current_voice_stream.stop()
        ctx.bot.current_voice_stream = None

    @command(commands, 'stop', flags=[CommandFlags.PLUGIN])
    def command_stop(self, ctx):
        self.playlist_pull_event.clear()
        self.playlist.clear()

        ctx.bot.current_voice_stream.stop()
        ctx.bot.current_voice_stream = None
    
    @command(commands, 'vol', flags=[CommandFlags.PLUGIN])
    def command_vol(self, ctx, v):
        self.volume = float(v) / 100
        if ctx.bot.current_voice_stream:
            ctx.bot.current_voice_stream.volume = float(v) / 100
