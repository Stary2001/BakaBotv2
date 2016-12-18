#!/usr/bin/env python3

from config import Config
from irc.irc_bot import IRCBot
import eventlet

eventlet.monkey_patch()

bots = {}
config = None
try:
	config = Config('conf/main.yml')
except FileNotFoundError:
	print("config not found :(")
	exit()

for n in config.get('networks'):
	bots[n] = IRCBot(n)

pool = eventlet.GreenPool(100)

for n in bots:
	bots[n].run(pool)

pool.waitall()