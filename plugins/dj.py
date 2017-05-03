from command import command, CommandFlags
from plugin import Plugin
import discord
import asyncio
import datetime

class DJPlugin(Plugin):
    commands = {}

    def __init__(self, bot):
        super().__init__(bot)
        if bot.type != 'discord':
            return
        self.bot = bot

        self.playlist = asyncio.Queue()
        self.playlist_coro = asyncio.get_event_loop().create_task(self.do_playlist())
        self.announce_channel = None
        self.volume = 1.0

    def exit(self):
        self.playlist_coro.cancel()

    async def do_playlist(self):
        while True:
            item = await self.playlist.get()

            if self.bot.discord_voice:
                if item[0] == 'yt':
                    playing_event = asyncio.Event()

                    player = await self.bot.discord_voice.create_ytdl_player(item[1], after=lambda: playing_event.set())
                    self.bot.current_voice_stream = player
                    player.start()
                    player.volume = self.volume

                    hours, min_sec = divmod(player.duration, 3600)
                    minutes, seconds = divmod(min_sec, 60)

                    if hours != 0:
                        duration = "{:02d}h{:02d}m{:02d}s".format(hours, minutes, seconds)
                    elif minutes != 0:
                        duration = "{:02d}m{:02d}s".format(minutes, seconds)
                    else:
                        duration = "{:02d}s".format(seconds)

                    self.bot.send_message(self.announce_channel, 'Now playing: {} ({})'.format(player.title, duration))
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
    
    @command(commands, 'play', is_async = True, flags=[CommandFlags.PLUGIN])
    async def command_play(self, ctx, url):
        self.announce_channel = ctx.target
        await self.playlist.put(('yt', url))

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

    @command(commands, 'stop')
    def command_stop(ctx):
        while not self.playlist.empty(): # Clear the playlist.
            self.playlist.get_nowait()

        ctx.bot.current_voice_stream.stop()
        ctx.bot.current_voice_stream = None
    
    @command(commands, 'vol', flags=[CommandFlags.PLUGIN])
    def command_vol(self, ctx, v):
        self.volume = float(v) / 100
        if ctx.bot.current_voice_stream:
            ctx.bot.current_voice_stream.volume = float(v) / 100