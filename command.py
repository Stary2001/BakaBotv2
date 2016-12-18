class Command():
	def __init__(self, name, f):
		self.name = name
		self.f = f

	def __call__(self, *args, **kwargs):
		return self.f(*args, **kwargs)

class CommandCtx():
	def __init__(self, bot, target, sender):
		self.bot = bot
		self.target = target
		self.sender = sender

	def reply(self, text):
		self.bot.send_message(self.target, text)

	def quit(self, text):
		self.bot.quit(text)