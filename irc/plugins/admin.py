from irc.irc_bot import command
from irc.plugin import Plugin

class AdminPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)
		for k in self.commands:
			self.bot.commands[k] = self.commands[k]

	@command(commands, 'ping')
	def command_ping(ctx):
		ctx.reply('pong')

	@command(commands, 'quit')
	def command_quit(ctx):
		ctx.quit('hi mom')