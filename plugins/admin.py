from bot import Bot
from command import command, CommandFlags
from plugin import Plugin
import asyncio

class AdminPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'quit', flags=[CommandFlags.ONE_PARAM])
	def command_quit(ctx, reason='Quitting...'):
		ctx.quit(reason)
		if len(Bot.get_all()) == 1:
			loop = asyncio.get_event_loop()
			loop.stop()

	@command(commands, 'quit_all', is_async = True)
	async def command_quit_all(ctx):
		for b in Bot.get_all():
			Bot.get(b).exit()

		await asyncio.sleep(2)

		loop = asyncio.get_event_loop()
		loop.stop()

	@command(commands, 'load')
	def command_load(ctx, name):
		ctx.bot.load_plugin(name)

	@command(commands, 'join')
	def command_join(ctx, name):
		ctx.bot.join(name)

	@command(commands, 'part')
	def command_part(ctx, name, msg=None):
		ctx.bot.part(name, msg)

	@command(commands, 'config')
	def command_config(ctx, where, meth, what, val=None):
		def usage():
			ctx.reply("Usage: config [local|shared] [get|set|add|del] (value?)")

		if where == 'local':
			conf = ctx.bot.local_config
		elif where == 'shared':
			conf = ctx.bot.shared_config
		else:
			usage()
			return

		k = what
		v = conf.get(k)
		if v == None:
			if meth == 'add':
				v = []
				conf.set(k, v)
			else:
				ctx.reply("Does not exist!")

		if meth == 'get':
			ctx.reply('{}: {}'.format(k, repr(conf.get(k))))
		elif val != None:
			if meth == 'set':
				ctx.reply('set {} to {}'.format(k, val))
				conf.set(k, val)
			elif meth == "add":
				ctx.reply("{} added to {}".format(val, k))
				v.append(val)
			elif meth == "del":
				ctx.reply("{} deleted from {}".format(val, k))
				v.remove(val)
			else:
				usage()
				return

			conf.save()
		else:
			usage()

	@command(commands, 'plugins')
	def command_plugins(ctx):
		ctx.reply(",".join(list(ctx.bot.plugins.keys())))
