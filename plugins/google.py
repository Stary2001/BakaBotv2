from command import command, CommandFlags
from plugin import Plugin
import requests
import json

class GoogleResult():
	def __init__(self, blob):
		self.blob = blob

	def __str__(self):
		return "{} | {}".format(self.blob['title'], self.blob['link'])

class GooglePlugin(Plugin):
	commands = {}

	def __init__(self, bot):
		super().__init__(bot)

	@command(commands, 'google', flags=[CommandFlags.ONE_PARAM])
	def command_google(ctx, query):
		k = ctx.bot.config.get('google.api_key')
		customid = ctx.bot.config.get('google.cx')

		r = requests.get("https://www.googleapis.com/customsearch/v1", params={'q': query, 'key': k, 'cx': customid})
		if r.status_code == 200:
			info = json.loads(r.text)
			if len(info['items']) == 0:
				ctx.reply("No results!")
				return []
			else:
				return [GoogleResult(info['items'][0])]
		else:
			ctx.reply("Google API request failed!")
			err = json.loads(r.text)
			ctx.reply(err["error"]["message"])