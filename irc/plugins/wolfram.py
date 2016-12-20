from command import command, CommandFlags
from irc.plugin import Plugin
import requests
from bs4 import BeautifulSoup
import re

class WolframResult():
	def __init__(self, blob):
		self.blob = blob

	def __str__(self):
		print(self.blob)
		plain = self.blob.find('plaintext')
		if plain and plain.get_text() != '':
			return plain.get_text()
		else:
			img = self.blob.find('img')
			if img:
				return img.get('src')
			else:
				return ":( i don't know how to parse {}".format(self.blob.get('id'))

class WolframPlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'wolfram', flags=[CommandFlags.ONE_PARAM])
	def command_google(ctx, query):
		app = ctx.bot.config.get('wolfram.app_id')

		r = requests.get("http://api.wolframalpha.com/v2/query", params={'appid': app, 'input': query, 'format': 'plaintext,image'})
		if r.status_code == 200:
			info = BeautifulSoup(r.text, 'xml')
			pri_pod = info.find('pod', primary=True)
			if pri_pod:
				return [WolframResult(pri_pod)]
			else:
				graph = info.find('pod', id=re.compile('Plot$'))
				if graph:
					return [WolframResult(graph)]
				else:
					ctx.reply("Wolfram Alpha doesn't understand that. :(")
		else:
			ctx.reply("Wolfram Alpha API request failed!")