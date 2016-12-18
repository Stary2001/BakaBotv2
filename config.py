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

	def save(self):
		with open(name, 'r') as stream:
			try:
				yaml.dump(self.config, stream)
			except yaml.YAMLError as exc:
				print(exc)
