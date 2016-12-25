from command import command, CommandFlags
from irc.plugin import Plugin
import random
from eventlet import greenthread

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

	@command(commands, 'remind', flags=[])
	def command_remind(ctx, t, *msg):
		msg = ' '.join(msg)
		t = int(t)
		greenthread.spawn_after(t, lambda: ctx.reply("timer '{}' is up!".format(msg)))
		ctx.reply("Timer in {} for '{}' added.".format(time, msg))
