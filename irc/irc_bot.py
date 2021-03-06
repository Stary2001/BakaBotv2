from bot import Bot, callback
from command import Command, CommandCtx
from config import Config
import asyncio
import socket
from collections import namedtuple
import time

IRCLine = namedtuple('IRCLine', ['sender', 'command', 'params'])

import irc.sasl

class ModeGroup:
	def __init__(self, bot, mode):
		self.mode_char = bot.mode_map[mode]
		self.bot = bot

	def check(self, user, chan):
		if user.nick in chan.user_modes and self.mode_char in chan.user_modes[user.nick]:
			return True
		return False

class IRCUser():
	""" user = internal name, nick = display name """
	def __init__(self, nick, account=None):
		self.user = nick
		self.nick = nick
		self.account = account
		self.realname = None
		self.ident = None
		self.host = None
		self.synced = False

		self.channels = []
		self.groups = {}

	def __str__(self):
		return self.nick

class IRCChannel():
	def __init__(self, chan):
		self.name = chan
		self.users = []
		self.user_modes = {}
		self.modes = {}
	def __str__(self):
		return self.name

class IRCServer():
	def __init__(self):
		self.name = None
		self.version = None
		self.usermodes = None
		self.chanmodes = None
		self.supports_whox = False
		self.modes_per_line = 0
		self.modemap = {}

class IRCBot(Bot):
	default_handlers = {}

	def __init__(self, name, shared_config):
		self.type = 'irc'
		super().__init__(name)

		self.shared_config = shared_config
		self.local_config = Config('conf/irc/{name}.yml'.format(name=name))
		self.init_plugins()

		self.caps = {}
		self.mode_map = {}
		self.server = IRCServer()

		self.authenticated = False
		self.nick = self.local_config.get('irc.nickname')
		self.who_queue = asyncio.Queue()
		self.who_wait = 2

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
		self.sock_writer.write((l+'\r\n').encode('utf-8'))

	def send_message(self, target, text):
		self.send_line("PRIVMSG {} :{}", target, str(text))

	def join(self, chan):
		self.send_line("JOIN {}", chan)

	def part(self, chan, msg=None):
		if msg != None:
			self.send_line("PART {}", chan)
		else:
			self.send_line("PART {} :{}", chan, msg)

	def quit(self, text):
		self.send_line("QUIT :{}", text)

	async def run_loop(self):
		self.who_coro = self.loop.create_task(self.who_thread())

		host = self.local_config.get('irc.server.host')
		port = self.local_config.get('irc.server.port')
		use_ssl = self.local_config.get('irc.server.ssl')
		self.sock_reader, self.sock_writer = await asyncio.open_connection(host=host, port=port, ssl=use_ssl)

		self.send_line("CAP LS")

		while True:
			line = await self.sock_reader.readline()
			if line == b'':
				break

			line = line.decode('utf-8')
			line = line.strip()
			print("<<< " + line)
			line = self.parse_line(line)

			cmd = line.command.lower()
			await self.handle(cmd, line)

		self.who_coro.cancel()

	async def who_thread(self):
		while True:
			item = await self.who_queue.get()
			self.send_line("WHO " + item[1] + " %cuhnarsf")
			await asyncio.sleep(self.who_wait)

	def get_special_group(self, g):
		if g == 'op':
			return ModeGroup(self, 'o')
		elif g == 'voice':
			return ModeGroup(self, 'v')
		elif g == 'hop':
			return ModeGroup(self, 'h')
		else:
			return None

	def user_has_id(self, user, id):
		if user.account == id:
			return True

	def exit(self, msg="Quitting.."):
		self.quit(msg)

	@callback('irc/cap', ['param/1', 'param/2'], is_async=True)
	def cb_cap(self, event, what):
		if event == 'LS':
			self.caps = what.split(' ')
			return self.handle('cap-ls')
		elif event == 'ACK':
			return self.handle('has-cap-' + what)

	@callback('irc/cap-done')
	def cap_done(self):
		if self.local_config.get('irc.password'):
			self.send_line("PASS {pass}".format())
		self.send_line("NICK {name}", name=self.nick)
		irc_username = self.local_config.get('irc.username')
		irc_realname = self.local_config.get('irc.realname')
		self.send_line("USER {user} * * :{real}", user=irc_username, real=irc_username)

	@callback('irc/004', ['param/1', 'param/2', 'param/3'])
	def cb_myinfo(self, srv_name, srv_version, usermodes):
		self.server.name = srv_name
		self.server.version = srv_version
		self.server.usermodes = list(usermodes)
		# we get channel modes in 005.

	@callback('irc/005')
	def cb_isupport(self, line):
		for s in line.params:
			if s.startswith("CHANMODES"):
				self.server.chanmodes = {}
				s = s[s.find('=')+1:]
				s = s.split(',')
				self.server.chanmodes['list'] = list(s[0])
				self.server.chanmodes['alwaysparam'] = list(s[1])
				self.server.chanmodes['setparam'] = list(s[2])
				self.server.chanmodes['neverparam'] = list(s[3])
			elif s.startswith("PREFIX"):
				s = s.split('=')[1]
				prefixes = s[s.find(')')+1:]
				modes = s[1:s.find(')')]
				self.server.mode_map = dict(zip(modes, prefixes))
				self.server.chanmodes['list'] += modes
			elif s == 'WHOX':
				self.server.supports_whox = True
			elif s.startswith('NETWORK'):
				self.server.name = s.split('=')[1]
			elif s.startswith('MODES'):
				self.server.modes_per_line = int(s.split('=')[1])

	@callback('irc/ping', ['param/0'])
	def cb_ping(self, code):
		self.send_line("PONG :{code}", code=code)

	@callback('irc/376', [], is_async=True)
	def end_of_motd(self):
		return self.handle('connected')

	@callback('irc/connected')
	def connected(self):
		if self.local_config.get('irc.autojoin'):
			for c in self.local_config.get('irc.autojoin'):
				self.join(c)

	def get_user(self, nick):
		if not nick in self.users:
			self.users[nick] = IRCUser(nick)
		return self.users[nick]

	def get_channel(self, chan):
		if not chan in self.channels:
			self.channels[chan] = IRCChannel(chan)
		return self.channels[chan]

	@callback('irc/privmsg', ['sender', 'param/0', 'param/1'], is_async=True)
	def command_handler(self, sender, target, content):
		if target == self.nick: # pm?
			target = sender
		else:
			target = self.get_channel(target)
		return self.handle('message', sender, target, content)

	@callback('irc/join', ['param/0', 'sender'], is_async = True)
	def cb_join(self, chan, user):
		if user.nick == self.nick:
			# ok, WE joined.
			return self.who_queue.put(('chan', chan))
		else:
			user.channels.append(chan)
			c = self.get_channel(chan)
			c.users.append(user)
			c.user_modes[user] = []
			if not user.synced:
				return self.who_queue.put(('user', user.nick, chan))

	@callback('irc/part', ['param/0', 'sender'])
	def cb_part(self, chan, user):
		if user.nick == self.nick:
			# ok, we ... left?
			pass
		else:
			user.channels.remove(chan)
			c = self.get_channel(chan)
			c.users.remove(user)
			if user.nick in c.user_modes:
					del c.user_modes[user.nick]

	@callback('irc/quit', ['sender'])
	def cb_quit(self, user):
		for chan in user.channels:
			c = self.get_channel(chan)
			c.users.remove(user)
			if user.nick in c.user_modes:
				del c.user_modes[user.nick]
		del self.users[user.nick]

	@callback('irc/error') # We will always get an ERROR on disconnect (like ERROR :Closing Link: ip (Client Quit) on quit or so)
	def cb_error(self, message):
		Bot.exit(self)

	@callback('irc/352', ['param/1', 'param/2', 'param/3', 'param/4', 'param/5', 'param/6', 'param/7'])
	@callback('irc/354', ['param/1', 'param/2', 'param/3', 'param/4', 'param/5', 'param/6', 'param/7', 'param/8'])
	def cb_who(self, channel, ident, host, server, nick, modes, account_maybe, realname_maybe=None):
		user = self.get_user(nick)
		user.ident = ident
		user.host = host

		if realname_maybe != None:
			user.account = account_maybe
			user.realname_maybe = realname_maybe
		else:
			user.realname = account_maybe
			user.account = None

		if channel != "*":
			user.channels.append(channel)
			chan = self.get_channel(channel)
			chan.users.append(user)
			if not nick in chan.user_modes:
				chan.user_modes[nick] = []

			chan.user_modes[nick] += list(modes)
			chan.user_modes[nick] = list(set(chan.user_modes[nick])) # eliminate dupes

			user.synced = True

		#print(channel, ident, host, server, nick, modes, realname_maybe, account_maybe)

	@callback('irc/mode')
	def cb_mode(self, line):
		target = line.params[0]
		modes = line.params[1:]
		if not target.startswith('#'):
			return # usermodes are todo

		modes_iter = iter(modes)
		for o in modes_iter:
			for oo in o:
				add = o[0] == '+'

				if oo in self.server.mode_map:
					c = self.get_channel(target)
					nick = next(modes_iter)
					mode_char = self.server.mode_map[oo]

					# not really needed, but ok
					if not nick in c.user_modes:
						c.user_modes[nick] = []

					if add:
						if not mode_char in c.user_modes[nick]:
							c.user_modes[nick].append(mode_char)
					else:
						if mode_char in c.user_modes[nick]:
							c.user_modes[nick].remove(mode_char)

					continue
	# todo: channelmode syncing of o/v works, need to implement banlists, +k etc


