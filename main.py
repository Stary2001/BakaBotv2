#!/usr/bin/env python3

from config import Config
from irc.irc_bot import IRCBot
import asyncio

bots = {}
config = None
try:
	config = Config('conf/main.yml')
except FileNotFoundError:
	print("config not found :(")
	exit()

for n in config.get('networks'):
	bots[n] = IRCBot(n)

loop = asyncio.get_event_loop()
for n in bots:
	bots[n].run(loop)

loop.run_forever()