from irc.irc_bot import command
from irc.plugin import Plugin

class UtilPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'ping')
	def command_ping(ctx):
		ctx.reply('pong')

	@command(commands, 'quit')
	def command_quit(ctx):
		ctx.quit('hi mom')