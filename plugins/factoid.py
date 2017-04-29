from command import command, CommandFlags
from plugin import Plugin

class FactoidPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'setf')
	def command_set_factoid(ctx, name, *value):
		value = ' '.join(value)
		ctx.bot.shared_config.set('factoids.{}'.format(name), value)
		ctx.bot.shared_config.save()

	@command(commands, 'f')
	def command_set_factoid(ctx, name):
		text = ctx.bot.shared_config.get('factoids.{}'.format(name))
		if text != None:
			ctx.reply(text)
		else:
			ctx.reply("Factoid '{}' not found!".format(name))

	@command(commands, 'delf')
	def command_del_factoid(ctx, name, *value):
		value = ' '.join(value)
		ctx.bot.shared_config.remove('factoids.{}'.format(name))
		ctx.bot.shared_config.save()