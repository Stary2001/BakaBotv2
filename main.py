#!/usr/bin/env python3

from bot import Bot
from config import Config
from irc.irc_bot import IRCBot
from discord_bot.discord_bot import DiscordBot, CustomDiscordClient

import asyncio

config = None
try:
    config = Config('conf/main.yml')
    shared_conf = Config('conf/shared.yml')
except FileNotFoundError:
    print("config not found :(")
    exit()

if config.get('bots.irc'):
    for n in config.get('bots.irc'):
       Bot.add(n, IRCBot(n, shared_config = shared_conf))

if config.get('bots.discord'):
    Bot.add('discord', DiscordBot('discord', shared_config = shared_conf))

if len(Bot.get_all()) != 0:
    loop = asyncio.get_event_loop()
    for n in Bot.get_all():
        Bot.get(n).run(loop)

    loop.run_forever()