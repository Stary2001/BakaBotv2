from command import command, CommandFlags
from plugin import Plugin
import discord
import socket

class DJPlugin(Plugin):
    commands = {}

    def __init__(self, bot):
        super().__init__(bot)
        if bot.type != 'discord':
            return

    @command(commands, 'join_voice', is_async = True)
    async def command_join_voice(ctx, name):
        channel = discord.utils.find(lambda c: c.name == name and c.type == discord.ChannelType.voice, ctx.target.server.channels)
        if not channel:
            return

        if ctx.bot.discord_voice:
            await ctx.bot.discord_voice.move_to(channel)
        else:
            ctx.bot.discord_voice = await ctx.bot.discord.join_voice_channel(channel)
    
    @command(commands, 'play', is_async = True)
    async def command_play(ctx, url):
        player = await ctx.bot.discord_voice.create_ytdl_player(url)
        ctx.bot.current_voice_stream = player
        player.start()

    @command(commands, 'stop')
    def command_stop(ctx):
        ctx.bot.current_voice_stream.stop()
        ctx.bot.current_voice_stream = None
    
    @command(commands, 'vol')
    def command_vol(ctx, v):
        if ctx.bot.current_voice_stream:
            ctx.bot.current_voice_stream.volume = float(v) / 100