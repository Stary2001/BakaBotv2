from bot import Bot, callback
from command import Command, CommandCtx
import eventlet
from collections import namedtuple

eventlet.monkey_patch()

IRCLine = namedtuple('IRCLine', ['sender', 'command', 'params'])

import irc.sasl

class IRCUser():
	""" user = internal name, nick = display name """
	def __init__(self, nick):
		self.user = nick
		self.nick = nick

	def __str__(self):
		return self.nick

class IRCChannel():
	def __init__(self, chan):
		self.name = chan

	def __str__(self):
		return self.name

class IRCBot(Bot):
	default_handlers = {}

	def __init__(self, name):
		self.type = 'irc'
		super().__init__(name)
		self.caps = {}
		self.authenticated = False
		autoload = self.config.get("autoload")
		if autoload != None:
			for p in autoload:
			  self.load_plugin(p)
		else:
			self.load_plugin("admin")

	def readlines(self, recv_buffer=4096, delim=b'\r\n'):
		buffer = b''
		data = True
		while data and self.running:
			data = self.sock.recv(recv_buffer)
			buffer += data

			while buffer.find(delim) != -1:
				line, buffer = buffer.split(delim, 1)
				yield line.decode('utf-8')
		return

	def parse_line(self, line):
		read_sender = False
		read_cmd = False

		sender = None
		cmd = None

		params = []
		last_space = 0

		for i in range(0, len(line)+1):
			if i == len(line) or line[i] == ' ':
				if line[0] == ':' and not read_sender:
					read_sender = True
					sender = line[last_space+1:i]
				elif not read_cmd:
					read_cmd = True
					cmd = line[last_space:i]
				else:
					if line[last_space] == ':':
						params.append(line[last_space+1:])
						break
					else:
						params.append(line[last_space:i])

				last_space = i + 1

		return IRCLine(sender=sender, command=cmd, params=params)

	def send_line(self, l, *args, **kwargs):
		l = l.format(*args, **kwargs)
		print(">>>" + l)
		self.sock.send((l+'\r\n').encode('utf-8'))

	def send_message(self, target, text):
		self.send_line("PRIVMSG {} :{}", target, text)

	def join(self, chan):
		self.send_line("JOIN {}", chan)

	def quit(self, text):
		self.send_line("QUIT :{}", text)

	def run_loop(self):
		self.sock = eventlet.connect((self.config.get('server.host'), self.config.get('server.port')))
		self.send_line("CAP LS")

		for line in self.readlines():
			print("<<< " + line)
			line = self.parse_line(line)
			cmd = line.command.lower()
			self.handle(cmd, line)

	@callback('irc/cap', ['param/1', 'param/2'])
	def cb_cap(self, event, what):
		if event == 'LS':
			self.caps = what.split(' ')
			self.handle('cap-ls')
		elif event == 'ACK':
			self.handle('has-cap-' + what)

	@callback('irc/cap-done')
	def cap_done(self):
		if self.config.get('irc.password'):
			self.send_line("PASS {pass}".format())
		self.send_line("NICK {name}", name=self.config.get('irc.nickname'))
		self.send_line("USER {user} * * :{real}", user=self.config.get('irc.username'), real=self.config.get('irc.realname'))

	@callback('irc/ping', ['param/0'])
	def cb_ping(self, code):
		self.send_line("PONG :{code}", code=code)

	@callback('irc/376', [])
	def end_of_motd(self):
		self.handle('connected')

	@callback('irc/connected')
	def connected(self):
		if self.config.get('irc.autojoin'):
			for c in self.config.get('irc.autojoin'):
				self.join(c)

	@callback('irc/privmsg', ['sender', 'param/0', 'param/1'])
	def command_handler(self, sender, target, content):
		sender = IRCUser(sender)
		target = IRCChannel(target)
		self.handle('message', sender, target, content)