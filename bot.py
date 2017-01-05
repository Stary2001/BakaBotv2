import eventlet
from config import Config
import importlib, inspect
from functools import wraps
from command import CommandCtx, CommandFlags, CommandNotFoundError, NoPermissionsError, AllGroup

default_handlers = {'irc': {}, 'bot': {}}

def callback(cb, params = None):
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
						p = line.sender
					my_args.append(p)
				return f(self, *my_args, **kwargs)
			else:
				return f(self, *args, **kwargs)

		handlers[cb] = handlers.get(cb, []) + [b]

		return b
	return a

class Bot:
	def __init__(self, name):
		global default_handlers
		self.name = name
		self.event_queue = eventlet.queue.Queue()
		self.config = Config('conf/networks/{name}.yml'.format(name=name))
		self.running = True
		self.handlers = default_handlers['bot'].copy()
		if self.type:
			self.handlers.update(default_handlers[self.type])	
		self.plugins = {}
		self.plugin_modules = {}
		self.commands = {}
		self.users = {}
		self.channels = {}

	def run(self, pool):
		pool.spawn_n(lambda: self.run_loop())

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
					

	def handle(self, n, *args):
		if n in self.handlers:
			for a in self.handlers[n]:
				a(self, *args)

	def check_permissions(self, user, cmd, target):
		allowed_groups = self.config.get('permissions.{}.groups'.format(cmd.name), [])
		allowed_groups = map(lambda x: self.get_group(x), allowed_groups)

		for g in allowed_groups:
			if g.check(user, target):
				return True

		cmd.allowed_users = self.config.get('permissions.{}.users'.format(cmd.name), [])
		for u in cmd.allowed_users:
			if user.account == u:
				return True

		return False

	@callback('message')
	def command_handler(self, sender, target, content):
		prefixes = self.config.get('irc.prefixes')
		for p in prefixes:
			if content.startswith(p):
				content = content[len(p):]
				cmds = content.split('|')
				cmds = list(map(lambda x: x.strip(), cmds))

				print(cmds)

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
							ret = self.commands[name](ctx, *other)
							if ret == None:
								ret = []
						else:
							# wrong type!
							pass
							
					if ret != None:
						for a in ret:
							self.send_message(target, str(a))
				except Exception as e:
					self.send_message(target, 'Exception thrown: "{}"'.format(str(e)))
				
	def get_group(self, g):
		if g.startswith('special/'):
			g = g[g.find('special/')+len('special/'):]
			if g == 'all':
				return AllGroup()
			else:
				return self.get_special_group(g)
		else:
			return self.groups[g]

	def get_special_group(self, g):
		""" override this """
		pass

	def send_message(self, target, text):
		"""
			send_message: Sends a message 'text' to 'target'.
		"""
		pass