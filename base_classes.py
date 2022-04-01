# from twitchio.ext import commands
from twitchio.ext.commands import Context
# from twitchio import channel, chatter, FollowEvent, ChannelInfo, Clip, User
import random
# import re
# import os
from collections import namedtuple
import sqlite3
from textwrap import dedent
from typing import Callable, Sequence
from db._create_tables import _create_tables
import my_commands.built_ins as built_in_commands
# import my_commands.default_commands as default_commands
from my_commands import string_commands
# import atexit
# from dotenv import load_dotenv
import parse_cmd

_db_file = "db/botdb.db"


class AssignmentError(Exception): ...
class RegistrationError(AssignmentError): ...
class DatabaseError(Exception): ...


_channel_field_names = '''
    channel_id username display_name commands '''.split()
# _channel_field_names += '''built_ins users variables'''.split()
_channel_nt = namedtuple('RegisteredChannel', _channel_field_names,
                         defaults=[{}] * (len(_channel_field_names) - 3))


class RegisteredChannel(_channel_nt):
    # @property
    # def commands(self):
    #     return self._commands
    pass


_command_field_names = '''
    channel_id name message aliases perms count is_hidden override_builtin
    is_enabled author_id modified_by modified_on ctime mtime
    '''.split()
_command_nt = namedtuple('RegisteredCommand', _command_field_names,
                         defaults=[None] * (len(_command_field_names) - 2))


class RegisteredCommand(_command_nt):
    # def __repr__(self) -> str:
    #     return 'REGISTERED COMMAND REPR'
    pass


class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
    channel_data: dict

    def __init__(self):
        self._init_database(_db_file)
        self._init_channels()
        self._init_commands()
        # self._init_built_ins()

    async def _event_ready(self):
        # Print a message to the console upon connection:
        print(f"{self.display_name} is online!")
        # Post a message in each registered channel's chat upon connection:
        # for channel in self.connected_channels:
        # notify = f"{self.display_name} is online!"
        #     await self.get_channel(channel).send(msg)
        #     pass

    # Maybe add this and other event handlers to a cog in bot.py:
    async def _event_message(self, message):
        # Messages sent by the bot have `echo` = True.
        # Ignore bot messages:
        if message.echo:
            return

        msg: str = message.content
        # Do imdad():
        if msg[:6].lower().startswith(("i'm ", "i am ", "im ")):
            if random.random() < 0.2:
                await message.channel.send(string_commands.imdad(msg))
        # Channel triggers and keywords can eventually be handled here as well.

        await self.handle_commands(message)

    async def _global_before_invoke(self, ctx: Context):
        # Set some useful values as Context attributes:
        channel = await ctx.channel.user()
        ctx.cmd, _, ctx.msg = ctx.message.content.partition(' ')
        ctx.author_id = int(ctx.author.id)
        ctx.chan_as_user = channel
        # ctx.channel_copy = self.regd_channels.get(channel.id)
        print(ctx.cmd, channel.id, channel.display_name)

    @property
    def channels(self):
        '''A list of registered channel names.'''
        # names += ENV['INITIAL_CHANNELS']
        return [c.username for c in self.regd_channels.values()]

    def _init_database(self, db_file: str):
        '''Connects to the sqlite3 database and creates tables if necessary.'''
        self._db_conn = sqlite3.connect(db_file)
        self._db = self._db_conn.cursor()
        with self._db_conn:
            for stmt in _create_tables:
                self._db.execute(stmt)
        self._built_ins = {k: v for k, v in built_in_commands.__dict__.items()
                           if isinstance(v, Callable)}
        self.built_ins = [f.__name__ for f in self._built_ins.values()
                          if not f.__name__.startswith('_')]
        # self._defaults = {k: v for k, v in default_commands.__dict__.items()
        #                   if isinstance(v, Callable)}
        # self.defaults = [f.__name__ for f in self._defaults.values()
        #                  if not f.__name__.startswith('_')]

    def _init_channels(self):
        '''Retrieves channel records from the database and initializes a
        `RegisteredChannel` object for each.'''
        records = self._db.execute("select * from channel")
        self.regd_channels = {}
        for record in records:
            channel_id = record[0]
            self.regd_channels[channel_id] = RegisteredChannel(*record)

    def _init_commands(self):
        '''Retrieves command records from the database and initializes a
        `RegisteredCommand` object for each.'''
        fields = ','.join(_command_field_names)
        row = "where override_builtin = None"
        row = ""
        _sql = f"select {fields} from command {row}"
        records = self._db.execute(_sql)
        for record in records:
            cmd = RegisteredCommand(*record)
            self.regd_channels[cmd.channel_id].commands[cmd.name] = cmd

    def _join_channel(self, ctx: Context):
        '''Registers a new channel and adds it to the IRC bot's list of joined
        channels when invoked within the bot's Twitch channel, then returns the
        response and username for `commands.Bot.join_channels()`.'''
        resp = ""
        username = ctx.author.name
        display_name = ctx.author.display_name
        if ctx.author_id not in self.regd_channels:
            try:
                # First, enter the channel into the database and memory:
                self._register_channel(ctx.author_id, username, display_name)
                # Then, add the channel to the IRC bot's joined channels list:
                resp = "I've successfully joined your channel. See you there!"
                print(f"Registered new channel {display_name}")
                print(self.regd_channels)
            # except RegistrationError as exc:
            #     resp = f"RegistrationError: {exc.args[0]}"
            # except sqlite3.Error as exc:
            #     resp = f"DatabaseError: {exc.args[0]}"
            except Exception as exc:
                print(exc.args[0])
                resp = f"""
                An unexpected error occurred while attempting to
                join your channel: {exc.args[0]}"""
        else:
            resp = "I am already in your channel!"
        return resp, username

    def _register_channel(self, uid: int, username: str, display_name: str):
        '''Registers a channel to the database if new, otherwise raises
        `RegistrationError`. This must only be called by a command invoked in
        the bot's channel.'''
        if uid in self.regd_channels:
            err = f"Channel {username} is already registered."
            raise RegistrationError(err)
        channel = RegisteredChannel(uid, username, display_name)
        self.regd_channels[uid] = channel
        fields = ('id', 'name', 'display_name')
        _sql = f"insert into channel({','.join(fields)}) values (?,?,?)"
        try:
            with self._db_conn:
                self._db.execute(_sql, (uid, username, display_name))
        except sqlite3.Error as exc:
            err = f"Failed registering channel {username!r}: {exc.args[0]}"
            raise DatabaseError(err)

    def _manage_custom_command(self, ctx: Context, built_in_name: str = 'cmd'):
        '''Parses a `!cmd` string and executes `_add_command()`,
        `_edit_command()` or `_delete_command()` based on the implied action.
        '''
        channel_id = ctx.chan_as_user.id
        if channel_id not in self.regd_channels:
            err = f"Channel with id {channel_id} is not registered."
            raise RegistrationError(err)

        action_switch = {a + built_in_name: a for a in 'add edit del'.split()}
        action_switch['del' + built_in_name] = 'delete'
        for a in 'disable enable alias'.split():
            action_switch[a] = a
        # self.action_switch = action_switch

        func_switch = {
            'add': self._add_command,
            'edit': self._edit_command,
            'delete': self._delete_command,
            'disable': self._edit_command,
            'enable': self._edit_command,
            # 'alias': self._edit_command
        }

        test_prefixes = {ctx.cmd.removeprefix(p) for p in ctx.prefix}
        prefixless = (lambda x: x[min(x)])({len(c): c for c in test_prefixes})
        action = ''
        msg = ctx.msg
        body = ctx.msg.split(None, 1)
        print("msg=", msg)
        print("body=", body)
        # if len(body) != 2:
            # try:
                # return parse_cmd.parse(body[0])
            # except Exception as exc:
                # print("Parser exception...", exc)
                # print(type(exc), exc.args[0])
        if prefixless == built_in_name:
            action, msg = body
            syntax = "<cmd syntax>"
            if action not in func_switch:
                err = f"Invalid action: {action!r}. Syntax: {syntax}"
                raise parse_cmd.InvalidAction(err)
        elif prefixless in action_switch:
            action = action_switch[prefixless]

        print("Action=", action)
        print("Msg=", msg)
        # try:
        parsed = parse_cmd.parse(msg=(action + ' ' + msg))

        if isinstance(parsed, tuple):
            cmd_info, message = parsed
        elif not parsed:
            err = """
            Parser returned NoneType, most likely resulting from a
            --help flag. Those will be implemented soon!"""
            raise TypeError(err)
        else:
            cmd_info = parsed
            message = None
        cmd = vars(cmd_info)
        channel_id = cmd['channel_id'] = ctx.chan_as_user.id
        # `cmd` will only have 'name' with 'add' or 'edit' actions.
        # 'name' will be a tuple when parsed; make it a str or None:
        cmd['name'] = cmd.get('name', [None])[0]
        cmd['message'] = message
        cmd['author_id'] = ctx.author_id
        if cmd.get('aliases'):
            cmd['aliases'] = ','.join(cmd['aliases'])
        cmd['used_shortcut'] = prefixless in action_switch
        # self.regd_channels[channel_id].commands[cmd['name']]['latest_modif'] = {
            # 'author_id': cmd['author_id'], 'used_shortcut': prefixless in action_switch
            # }

        for k, v in tuple(cmd.items()):
            if v is None:
                del cmd[k]
        print(cmd)

        if action in action_switch.values():
            return func_switch[action](cmd)

    def _add_command(self, cmd: dict):
        '''Adds a custom command to memory and the database.'''
        name = cmd['name']
        error_preface = f"Failed to register command {name!r}: "
        channel_id = cmd['channel_id']
        channel = self.regd_channels[channel_id]
        used_shortcut = cmd['used_shortcut']
        del cmd['used_shortcut']

        if name in channel.commands:
            err = f"""
            Command already exists.
            To change its message or properties, use
            {('!cmd edit', '!editcmd')[used_shortcut]!r}.
            """
            # Use '!cmd add -h' for details.
            # You can rename it with '!editcmd <oldname> --rename <newname>'.
            # To delete it completely, use '!delcmd'."""
            raise RegistrationError(error_preface + dedent(err))
        if name in self.built_ins:
            err = f"""
            Command name conflicts with a built-in command with the same name.
            Use '--override_builtin' if you want to replace it with your custom
            command. If you change your mind later,
            simply delete the custom command."""
            raise RegistrationError(error_preface + dedent(err))

        reqd_defaults = {
            'perms': 'everyone',
            'is_hidden': 0,
            'is_enabled': 1,
        }

        for k, v in reqd_defaults.items():
            cmd.setdefault(k, v)

        command = RegisteredCommand(**cmd)
        self.regd_channels[channel_id].commands[name] = command
        fields = ','.join(command._fields)
        vals = ','.join(['?'] * len(command._fields))
        _sql = f"insert into command({fields}) values ({vals})"
        try:
            with self._db_conn:
                self._db.execute(_sql, command)
        except sqlite3.Error as exc:
            err = f"DatabaseError: "
            raise DatabaseError(error_preface + err + exc.args[0])
        return f"Command {name!r} was added successfully."

    def _edit_command(self, cmd: dict):
        '''Alters a custom command's properties in memory and the database.'''
        name = cmd['name']
        error_preface = f"Falied to update command {name!r}: "
        channel_id = cmd['channel_id']
        channel = self.regd_channels[channel_id]
        if name not in channel.commands:
            err = f"This command does not exist. Use '!addcmd' to add it."
            raise RegistrationError(error_preface + dedent(err))
        if name in self.built_ins and not cmd['override_builtin']:
            err = f"""
            Command name conflicts with a built-in command with the same name.
            Use '--override_builtin' if you want to replace it with your custom
            command. If you change your mind later,
            simply delete the custom command."""
            raise RegistrationError(error_preface + dedent(err))
        old_command = channel.commands[name]._asdict()
        old_command.update(cmd)
        command = RegisteredCommand(**old_command)
        self.regd_channels[channel_id].commands[name] = command

        columns = ','.join(command._fields)
        placehds = ','.join(['?'] * len(command._fields))
        cond = f"(channel_id, name) = ({channel_id}, {name!r})"
        _sql = f"update command set({columns}) = ({placehds}) where {cond}"
        try:
            with self._db_conn:
                self._db.execute(_sql, command)
        except sqlite3.Error as exc:
            err = f"DatabaseError: {exc.args[0]}"
            raise DatabaseError(error_preface + dedent(err))
        # except Exception as exc:
            # print(exc.args[0])
            # err = f"""
            # An unexpected error occurred while updating command
            # {command.name!r}: """
            # return f"{err} {exc.args[0]}"
            # raise Exception(error_preface + err + exc.args[0])
        else:
            return f"Command {name!r} was edited successfully."

    def _delete_command(self, cmd):
        # error_preface = f"Unable to delete command {cmd['name']!r}: "
        pass

    def register_variable(self, varname: str):
        # _sql = "insert into variable(var_name) values (?)"
        # try:
        #     with self._db_conn:
        #         self._db.execute(_sql)
        #         self._db_conn.commit()
        # except sqlite3.Error as exc:
        #     print(exc.args[0])
        pass

    def set_chan_variable(self, varname, value):
        _sql = "update ..."
        pass


if __name__ == '__main__':

    bot = Yeetrbot()
    # print([channel.commands for channel in bot.regd_channels])
    # print([channel.__dict__ for channel in bot.regd_channels])
    # print([channel.__dict__ for channel in bot.regd_channels.values()])
    # print(bot.regd_channels)
    # print(bot.channels)
    # print(bot.regd_channels[0].commands[1].__dict__)
    # print([channel.commands for channel in bot.regd_channels])

    # bot._db_conn.commit()
