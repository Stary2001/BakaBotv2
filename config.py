import yaml

class Config():
	def __init__(self, name):
		self.filename = name

		with open(name, 'r') as stream:
			try:
				self.config = yaml.load(stream)
			except yaml.YAMLError as exc:
				print(exc)

	def get(self, path, default=None):
		path = path.split('.')
		item = self.config
		for p in path:
			try:
				item = item[p]
			except KeyError:
				return default
		return item

	def remove(self, path):
		path = path.split('.')
		item = self.config
		for p in path[0:-1]:
			try:
				item = item[p]
			except KeyError:
				return
		del item[path[-1]]
		return item

	def set(self, path, value):
		path = path.split('.')
		item = self.config

		for p in path[0:-1]:
			try:
				item = item[p]
			except KeyError:
				print("Creating.. ", p)
				item[p] = {}
				item = item[p]
		item[path[-1]] = value

	def save(self):
		with open(self.filename, 'w') as stream:
			try:
				yaml.dump(self.config, stream)
			except yaml.YAMLError as exc:
				print(exc)
