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

	@command(commands, 'auto')
	def command_auto(ctx, what, meth, name=None):
		k = None
		if what == 'join':
			k = 'irc.autojoin'
		elif what == 'load':
			k = 'autoload'
		else:
			return

		l = ctx.bot.config.get(k)
		if l == None:
			ctx.reply("List doesn't exist?")

		if meth == "add" and name != None:
			l.append(name)
			ctx.bot.config.save()
			ctx.reply("{} added.".format(name))
		elif meth == "del" and name != None:
			l.remove(name)
			ctx.bot.config.save()
			ctx.reply("{} deleted.".format(name))
		elif meth == "list":
			ctx.reply(", ".join(l))
		else:
			ctx.reply("Usage: auto [load|join] [add|del|list] (name?)")
