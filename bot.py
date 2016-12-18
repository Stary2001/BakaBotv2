import eventlet
from config import Config
import importlib, inspect
from functools import wraps
from command import CommandCtx

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


	def run(self, pool):
		pool.spawn_n(lambda: self.run_loop())

	def load_plugin(self, n):
		self.plugin_modules[n] = importlib.import_module('irc.plugins.' + n)
		loaded_plugins = inspect.getmembers(self.plugin_modules[n], inspect.isclass)
		for p in loaded_plugins:
			if p[0] != 'Plugin':
				self.plugins[n] = p[1](self)
				plug = self.plugins[n]
				for k in plug.commands:
					self.commands[k] = plug.commands[k]

	def handle(self, n, *args):
		if n in self.handlers:
			for a in self.handlers[n]:
				a(self, *args)

	@callback('message')
	def command_handler(self, sender, target, content):
		prefixes = self.config.get('irc.prefixes')
		for p in prefixes:
			if content.startswith(p):
				a = content.find(' ')
				other = None

				if a == -1: # remove prefix..
					name = content[len(p):]
				else:
					name = content[len(p):a]
					other = content[a+1:]
				
				if name in self.commands:
					if other == None:
						other = []
					else:
						other = other.split(' ')

					ctx = CommandCtx(self, target, sender)
					self.commands[name](ctx, *other)