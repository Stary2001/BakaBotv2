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

	@command(commands, 'config')
	def command_list(ctx, meth, what, val=None):
		def usage():
			ctx.reply("Usage: auto [load|join] [add|del|list] (value?)")

		k = what
		v = ctx.bot.config.get(k)
		if v == None:
			if meth == 'add':
				v = []
				ctx.bot.config.set(k, v)

		if meth == 'get':
			ctx.reply('{}: {}'.format(k, repr(ctx.bot.config.get(k))))
		elif val != None:
			if meth == 'set':
				ctx.reply('set {} to {}'.format(k, val))
				ctx.bot.config.set(k, val)
			elif meth == "add":
				ctx.reply("{} added to {}".format(val, k))
				v.append(val)
			elif meth == "del":
				ctx.reply("{} deleted from {}".format(val, k))
				v.remove(val)
			else:
				usage()
				return

			ctx.bot.config.save()
		else:
			usage()