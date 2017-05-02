#!/usr/bin/env python3

from bot import Bot
from config import Config
from irc.irc_bot import IRCBot
from discord_bot.discord_bot import DiscordBot, CustomDiscordClient

import asyncio

config = None
try:
    config = Config('conf/main.yml')
    Bot.shared_config = Config('conf/shared.yml')
except FileNotFoundError:
    print("config not found :(")
    exit()

if config.get('bots.irc'):
    for n in config.get('bots.irc'):
       Bot.start(IRCBot, n)

if config.get('bots.discord'):
    Bot.start(DiscordBot, 'discord')

if len(Bot.get_all()) != 0:
    loop = asyncio.get_event_loop()
    loop.run_forever()