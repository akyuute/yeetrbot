'''A module to independently test channel and command handling code.'''

import test_bc

class Obj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class Context:
    def __init__(self, prefix, cmd, msg):
        self.prefix = prefix
        self.cmd = cmd
        self.msg = msg
        self.chan_as_user = Obj(id=1234)
        self.author_id = 1234
    pass


mybot = test_bc.Yeetrbot()
mybot._init_database('db/bot.db')
mybot._init_channels()
mybot._init_commands()
# mybot._register_channel(1234, 'myname', 'MyName')
mybot._base_command_name = 'cmd'
mybot._default_perms = 'everyone'
mybot._default_count = 0
mybot._require_message = True
mybot._override_builtins = True

mybot._base_command_aliases = {'add': 'addcmd', 'edit': 'editcmd', 'delete': 'delcmd', 'disable': 'disable', 'enable': 'enable'}

ctx = Context(prefix='!')
