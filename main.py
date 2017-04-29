#!/usr/bin/env python3

from config import Config
from irc.irc_bot import IRCBot
from discord_bot.discord_bot import DiscordBot, CustomDiscordClient

import asyncio

bots = {}
config = None
try:
    config = Config('conf/main.yml')
    shared_conf = Config('conf/shared.yml')
except FileNotFoundError:
    print("config not found :(")
    exit()

if config.get('bots.irc'):
    for n in config.get('bots.irc'):
       bots[n] = IRCBot(n, shared_config = shared_conf)

if config.get('bots.discord'):
    bots['discord'] = DiscordBot('discord', shared_config = shared_conf)

if len(bots) != 0:
    loop = asyncio.get_event_loop()
    for n in bots:
        bots[n].run(loop)

    loop.run_forever()