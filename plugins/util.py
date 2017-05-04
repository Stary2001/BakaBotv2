from command import command, CommandFlags
from plugin import Plugin
import random
import asyncio

class UtilPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'ping')
	def command_ping(ctx):
		return ['pong']

	@command(commands, 'choose', flags=[CommandFlags.ONE_PARAM])
	def command_choose(ctx, choices):
		choices = choices.split(' or ')
		idx = random.randint(0, len(choices)-1)
		return [choices[idx]]

	@command(commands, 'remind', is_async=True)
	async def command_remind(ctx, t, *msg):
		msg = ' '.join(msg)
		t = int(t)
		ctx.reply("Timer in {} sec for '{}' added.".format(time, msg))
		await asyncio.sleep(t)
		ctx.reply("timer '{}' is up!".format(msg))