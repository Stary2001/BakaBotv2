from bot import callback
from bot import default_handlers

@callback('irc/cap-ls', is_async=True)
async def req_sasl(self):
	if self.config.get('server.nickserv') and 'sasl' in self.caps:
		self.send_line("CAP REQ sasl")
	else:
		self.send_line("CAP END")
		await self.handle('cap-done')

@callback('irc/has-cap-sasl')
def req_plain(self):
	self.send_line("AUTHENTICATE PLAIN")

@callback('irc/authenticate', ['param/0'])
def cb_authenticate(self, accepted):
	if accepted == "+": # accepted
		ns = self.config.get('server.nickserv')
		sasl_plain = base64.encode(b'baka\0' + ns['user'].encode('utf-8') + b'\0' + ns['pass'].encode('utf-8'))
		self.send_line("AUTHENTICATE " + sasl_plain)

@callback('irc/903', [])
def sasl_success(self):
	self.authenticated = True
	self.handle('cap-done')

@callback('irc/904', [])
def sasl_fail(self):
	self.authenticated = False
	self.handle('cap-done')