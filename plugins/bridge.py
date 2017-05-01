from bot import Bot
from command import command, CommandFlags
from plugin import Plugin

class BridgePlugin(Plugin):
    commands = {}

    def __init__(self, bot):
        super().__init__(bot)
        bot.add_handler('message', self.msg_handler, is_async=False, uses_self=True)
        bots = []

        self.mapping = {}

        bridges = bot.local_config.get('bridges')
        if bridges != None:
            for b in bridges:
                b = bridges[b]
                self.mapping[bot.get_channel(b['local'])] = BridgePlugin.get_channel(b['remote'])

    @staticmethod
    def get_channel(channeldef):
        c = channeldef.split('/')
        b = Bot.get(c[0])
        return {'bot': b, 'chan': b.get_channel(c[1]) }

    @command(commands, 'add_bridge')
    def command_add_bridge(ctx, name, local, remote): # sends from local to remote.
        ctx.bot.local_config.set('bridges.{}'.format(name), {'local': local, 'remote': remote})
        ctx.bot.local_config.save()
        #self.mapping[bot.get_channel(local)] = BridgePlugin.get_channel(remote)

    def msg_handler(self, bot, sender, target, content):
        try:
            if target in self.mapping:
                new_target = self.mapping[target]
                new_target['bot'].send_message(new_target['chan'], "<{}> {}".format(sender, content))
        except:
            pass