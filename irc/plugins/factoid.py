from command import command, CommandFlags
from irc.plugin import Plugin

class FactoidPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'setf')
	def command_set_factoid(ctx, name, *value):
		value = ' '.join(value)
		ctx.bot.config.set('factoids.{}'.format(name), value)
		ctx.bot.config.save()

	@command(commands, 'f')
	def command_set_factoid(ctx, name):
		text = ctx.bot.config.get('factoids.{}'.format(name))
		if text != None:
			return [text]
		else:
			return "Factoid '{}' not found!".format(name)

	@command(commands, 'delf')
	def command_del_factoid(ctx, name, *value):
		value = ' '.join(value)
		ctx.bot.config.remove('factoids.{}'.format(name))
		ctx.bot.config.save()