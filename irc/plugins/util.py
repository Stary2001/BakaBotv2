from command import command, CommandFlags
from irc.plugin import Plugin
import random

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