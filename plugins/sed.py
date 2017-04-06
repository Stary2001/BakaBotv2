from command import command, CommandFlags
from plugin import Plugin
from bot import callback, Handler
from collections import deque
import re

class SedPlugin(Plugin):
    commands = {}

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

        self.scrollback = {}
        bot.handlers['message'] = [Handler(f=lambda self2,a,b,c: self.cb(a,b,c), is_async=True)] + bot.handlers['message']
    
    queue_size = 100

    async def cb(self, sender, target, content):
        # todo: sed disable.

        if not target in self.scrollback:
            self.scrollback[target] = deque(maxlen = self.queue_size)

        q = self.scrollback[target]

        if content[0:2] == 's/':
            i = 2

            match = None
            match_pos = None
            replacement = None
            flags = None
            num_escapes = 0

            while True:
                i = content.find('/', i)
                
                if i != -1:
                    if content[i-1] == '\\' and num_escapes % 2 == 0:
                        i=i+1
                        num_escapes += 1
                        continue
                    else:
                        match = content[2:i]
                        match_pos = i+1
                        break
                else:
                    break

            if match != None:
                i = match_pos
                num_escapes = 0

                while True:
                    i = content.find('/', i)
                    if i != -1:
                        if content[i-1] == '\\' and num_escapes % 2 == 0:
                            i=i+1
                            num_escapes += 1
                            continue
                        else:
                            replacement = content[match_pos:i]
                            flags = content[i+1:]
                            break
                    else:
                        break

                if replacement == None:
                    replacement = content[match_pos:]

                print(match, replacement, flags)
                count = 1
                if flags != None and 'g' in flags:
                    count = 0

                try:
                    expr = re.compile(match)
                    for index, line in enumerate(q):
                        if re.search(expr, line[2]) != None:
                            m = re.sub(expr, replacement, line[2], count=count)
                            q[index] = (line[0], line[1], str(m))
                            self.bot.send_message(target, m)
                            return
                except re.error as e:
                    self.bot.send_message(target, "You broke it: {}".format(e))

            return # Don't log sed-like messages.

        if len(q) == self.queue_size:
            q.popright()
        q.appendleft((sender, target, content))

        return True