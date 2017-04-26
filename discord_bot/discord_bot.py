import asyncio
import discord

from config import Config
from bot import Bot, callback
from command import Command, CommandCtx

class CustomDiscordClient(discord.Client):
    def __init__(self, bot, loop=None):
        self.bot = bot
        super().__init__(loop=loop)

    async def on_message(self, message):
        if message.author != self.user:
            await self.bot.handle('message', message.author, message.channel, message.content)

class DiscordBot(Bot):
    default_handlers = {}

    def __init__(self, name):
        self.type = 'discord'
        super().__init__(name)

        self.config = Config('conf/discord.yml')
        self.init_plugins()

        #perms = discord.Permissions.text()
        #perms.update(change_nicknames = True)
        #print(discord.utils.oauth_url(self.config.get('discord.appid'), permissions=perms))

    async def run_loop(self):
        self.discord = CustomDiscordClient(self, loop = self.loop)
        await self.discord.login(self.config.get('discord.token'))
        self.loop.create_task(self.discord.connect())

    def send_message(self, target, text):
        # TODO: 'content' can be say, an embed.
        # TODO: maybe make this be a queue.
        print(text)
        self.loop.create_task(self.discord.send_message(target, str(text))) # ewwwwww :(.

    def user_has_id(self, user, id):
        if user.id == id or "<@{}>".format(user.id) == id: # TODO: hack
            return True