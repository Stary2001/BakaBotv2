def command(l, name, params = None, flags = None, bot = None):
	def a(f):
		c = Command(name, f, bot=bot, flags=flags)
		l[name] = c
		return c
	return a

class CommandNotFoundException(Exception):
	def __init__(self, name):
		super().__init__()
		self.name = name

	def __str__(self):
		return "Command '{}' not found!".format(self.name)

class Command():
	def __init__(self, name, f, bot=None, flags=None):
		self.name = name
		self.f = f
		self.flags = flags
		self.type = bot

	def __call__(self, *args, **kwargs):
		return self.f(*args, **kwargs)

class CommandCtx():
	def __init__(self, bot, target, sender):
		self.bot = bot
		self.target = target
		self.sender = sender
		self.queue = []

	def reply(self, text):
		self.bot.send_message(self.target, text)

	def push(data):
		self.queue.append(data)

	def pop(data):
		if len(self.queue) != 0:
			return self.queue.pop(0)

	def quit(self, text):
		self.bot.quit(text)

class CommandFlags:
	ONE_PARAM = 1