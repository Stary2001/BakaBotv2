import eventlet
from config import Config

class Bot:
	def __init__(self, name):
		self.name = name
		self.event_queue = eventlet.queue.Queue()
		self.config = Config('conf/networks/{name}.yml'.format(name=name))
		self.running = True
		self.handlers = {}

	def run(self, pool):
		pool.spawn_n(lambda: self.run_loop())