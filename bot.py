import asyncio
from config import Config
import importlib, inspect
from functools import wraps
from command import CommandCtx, CommandFlags, CommandNotFoundError, NoPermissionsError, AllGroup
from collections import namedtuple

Handler = namedtuple('Handler', ['uses_self', 'is_async', 'f'])

default_handlers = {'irc': {}, 'bot': {}}

def callback(cb, params = None, is_async=False, uses_self=True):
	global default_handlers
	namespace = None

	if cb.find('/') == -1:
		namespace = 'bot'
	else:
		namespace = cb[:cb.find('/')]
		cb = cb[cb.find('/')+1:]

	if namespace not in default_handlers:
		default_handlers[namespace] = {}
	handlers = default_handlers[namespace]

	def a(f):
		@wraps(f)
		def b(self, *args, **kwargs):
			if params != None:
				line = args[0]
				my_args = []
				p = None

				for k in params:
					if k.startswith("param/"):
						k = int(k[len("param/"):])
						p = line.params[k]
					elif k == "sender":
						idx = line.sender.find('!')
						p = self.get_user(line.sender[:idx])
					my_args.append(p)
				return f(self, *my_args, **kwargs)
			else:
				return f(self, *args, **kwargs)

		handlers[cb] = handlers.get(cb, []) + [Handler(f=b, is_async=is_async, uses_self=uses_self)]

		return b
	return a

class Bot:
	def __init__(self, name):
		global default_handlers
		self.name = name
		self.event_queue = asyncio.Queue()
		self.running = True
		self.handlers = default_handlers['bot'].copy()
		if self.type and self.type in default_handlers:
			self.handlers.update(default_handlers[self.type])
		self.plugins = {}
		self.plugin_modules = {}
		self.commands = {}
		self.users = {}
		self.channels = {}
		self.pool = None

	def add_handler(self, n, f, is_async=False, uses_self=False):
		self.handlers[n] = self.handlers.get(n, []) + [Handler(f=f, is_async=is_async, uses_self=uses_self)]

	def init_plugins(self):
		autoload = self.local_config.get("autoload")
		if autoload != None:
			for p in autoload:
			  self.load_plugin(p)
		else:
			self.load_plugin("admin")

	def run(self, loop):
		self.loop = loop
		loop.create_task(self.run_loop())

	def exit(self, msg=None):
		for name in self.plugins:
			plug = self.plugins[name]
			plug.exit()

		del Bot.get_all()[self.name]
		""" call super() before quitting in a subclass. """

	def load_plugin(self, n):
		if n in self.plugin_modules:
			importlib.reload(self.plugin_modules[n])
		else:
			self.plugin_modules[n] = importlib.import_module('plugins.' + n)

		loaded_plugins = inspect.getmembers(self.plugin_modules[n], inspect.isclass)
		for p in loaded_plugins:
			if p[1].__bases__[0].__name__ == 'Plugin':
				self.plugins[n] = p[1](self)
				plug = self.plugins[n]
				for k in plug.commands:
					self.commands[k] = plug.commands[k]
					self.commands[k].plugin = plug

	async def handle(self, n, *args):
		if n in self.handlers:
			for a in self.handlers[n]:
				if a.is_async:
					if a.uses_self:
						coro = a.f(self, *args)
					else:
						coro = a.f(*args)
					if coro != None:
						await coro
				else:
					if a.uses_self:
						a.f(self, *args)
					else:
						a.f(*args)

	def check_permissions(self, user, cmd, target):
		allowed_groups = self.local_config.get('permissions.{}.groups'.format(cmd.name), [])
		allowed_groups = map(lambda x: self.get_group(x), allowed_groups)

		for g in allowed_groups:
			if g.check(user, target):
				return True

		cmd.allowed_users = self.local_config.get('permissions.{}.users'.format(cmd.name), [])

		for allowed_id in cmd.allowed_users:
			if self.user_has_id(user, allowed_id):
				return True

		return False

	@callback('message', is_async = True)
	async def command_handler(self, sender, target, content):
		prefixes = self.local_config.get('prefixes')
		for p in prefixes:
			if content.startswith(p):
				content = content[len(p):]
				cmds = content.split('|')
				cmds = list(map(lambda x: x.strip(), cmds))

				ret = []
				try:
					for c in cmds:
						pos = c.find(' ')
						other = None
						if pos != -1:
							name = c[:pos]
							other = c[pos+1:]
						else:
							name = c

						if not name in self.commands:
							raise CommandNotFoundError(name)

						cmd = self.commands[name]
						if not self.check_permissions(sender, cmd, target):
							raise NoPermissionsError(name)

						if cmd.type == None or cmd.type == self.type:
							if other == None:
								other = []
							elif cmd.flags != None and CommandFlags.ONE_PARAM in cmd.flags:
								other = [other]
							else:
								other = other.split(' ')

							other += ret
							ctx = CommandCtx(self, target, sender)

							args = []
							if cmd.flags != None and CommandFlags.PLUGIN in cmd.flags:
								args = [cmd.plugin, ctx]
							else:
								args = [ctx]

							if cmd.is_async:
								ret = await cmd.f(*args, *other)
							else:
								ret = cmd.f(*args, *other)

							if ret == None:
								ret = []
						else:
							# wrong type!
							pass

					if ret != None:
						for a in ret:
							self.send_message(target, a)
				except Exception as e:
					self.send_message(target, '{} was thrown: "{}"'.format(e.__class__.__name__, str(e)))

	def get_group(self, g):
		if g.startswith('special/'):
			g = g[g.find('special/')+len('special/'):]
			if g == 'all':
				return AllGroup()
			else:
				return self.get_special_group(g)
		else:
			return self.groups[g]

	def user_has_id(self, user, identifier):
		""" override this. """
		return False

	def get_special_group(self, g):
		""" override this """
		pass

	def send_message(self, target, text):
		"""
			send_message: Sends a message 'text' to 'target'.
		"""
		pass

	def get_channel(self, chan):
		"""
			returns a channel obj for 'chan'.
		"""
		pass

	__bots = {}
	shared_config = None
	@staticmethod
	def add(n, b):
		Bot.__bots[n] = b

	@staticmethod
	def get(n):
		return Bot.__bots[n]

	def get_all():
		return Bot.__bots

	@staticmethod
	def start(t, name):
		Bot.add(name, t(name, shared_config=Bot.shared_config))
		Bot.get(name).run(asyncio.get_event_loop())

	@staticmethod
	def stop(name):
		Bot.get(name).exit()