from command import command, CommandFlags
from plugin import Plugin
import requests
import json

class IPInfo:
	def __init__(self, blob):
		self.blob = blob

	def __str__(self):
		s = self.blob['ip']
		if 'hostname' in self.blob and self.blob['hostname'] != 'No Hostname':
			s += " (" + self.blob['hostname'] + ")"
		if self.blob['city'] != '':
			s += " in {}, {}, {}".format(self.blob['city'], self.blob['region'], self.blob['country'])
		if self.blob['org'] != '':
			s += " hosted by {}".format(self.blob['org'])
		return s

class IPInfoPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'ipinfo')
	def command_ipinfo(ctx, *ips):
		l = []

		for ip in ips:
			r = requests.get("http://ipinfo.io/{}".format(ip))
			if r.status_code == 200:
				info = json.loads(r.text)
				l.append(IPInfo(info))

		return l
