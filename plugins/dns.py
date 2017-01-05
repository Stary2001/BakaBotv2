from command import command, CommandFlags
from plugin import Plugin
import socket

class DNSPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'dns')
	def command_dns(ctx, name):
		g = socket.getaddrinfo(name, 0, proto=socket.IPPROTO_TCP)
		l = list(map(lambda x: x[4][0], g))
		return l