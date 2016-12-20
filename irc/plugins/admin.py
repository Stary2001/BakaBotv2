from command import command, CommandFlags
from irc.plugin import Plugin

class AdminPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'quit', flags=[CommandFlags.ONE_PARAM])
	def command_quit(ctx, reason='Quitting...'):
		ctx.quit(reason)

	@command(commands, 'load')
	def command_load(ctx, name):
		ctx.bot.load_plugin(name)

	@command(commands, 'join')
	def command_join(ctx, name):
		ctx.bot.join(name)

	@command(commands, 'part')
	def command_part(ctx, name):
		ctx.bot.part(name)