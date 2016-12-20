from command import command
from irc.plugin import Plugin

class UtilPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'ping')
	def command_ping(ctx):
		return ['pong']