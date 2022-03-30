# from twitchio.ext import commands
from twitchio.ext.commands import Context
# from twitchio import channel, chatter, FollowEvent, ChannelInfo, Clip, User
import random
# import re
# import os
from collections import namedtuple
import sqlite3
from typing import Callable, Sequence
from db._create_tables import _create_tables
import my_commands.built_ins as built_in_commands
# import my_commands.default_commands as default_commands
from my_commands import string_commands
# import csv
# import atexit
# from os import environ
# from dotenv import load_dotenv
import parse_cmd

_db_file = "db/botdb.db"

class AssignmentError(Exception): ...
class RegistrationError(AssignmentError): ...
class DatabaseError(Exception): ...

_channel_field_names = '''
    channel_id username display_name commands '''.split() # built_ins users variables
_channel_nt = namedtuple('RegisteredChannel', _channel_field_names,
    defaults=[{}] * (len(_channel_field_names) - 3))
    # defaults=[{}, {}, {}, {}, ] ) # * len(_channel_field_names))
class RegisteredChannel(_channel_nt):
    # @property
    # def commands(self):
        # return self._commands
    pass

_command_field_names = '''
    channel_id name message aliases perms count is_hidden override_builtin
    is_enabled author_id modified_by modified_on ctime mtime
    '''.split()
_command_nt = namedtuple('RegisteredCommand', _command_field_names,
    defaults=[None] * (len(_command_field_names) - 2))

class RegisteredCommand(_command_nt):
    # def __repr__(self) -> str:
        # return 'REGISTERED COMMAND REPR'
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
        # Post a message in the console upon connection
        print(f"{self.display_name} is online!")
        # Also post a message in chat upon connection
        # for channel in self.connected_channels:
            # await self.get_channel(channel).send(f"{self.display_name} is online!")
            # pass

    # async def event(self, name: str = "imdad"):
        # return super().event(name)

    # Maybe add this and other event handlers to a cog in bot.py:
    async def _event_message(self, message):
        msg: str = message.content
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Do imdad():
        if str(message.content)[:6].lower().startswith(("i'm ", "i am ", "im ")):
            if random.random() < 0.2:
                await message.channel.send(string_commands.imdad(msg))


        # Print the contents of our message to console...
        # Also may be useful to append to a log file
        #####if message.echo:
        #print(message.content)

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    async def _global_before_invoke(self, ctx: Context):
        channel = await ctx.channel.user()
        # print(f"{super(commands.Bot).user_id = }")
        print(ctx.command.name, channel.id, channel.display_name)

        ctx.cmd, _, ctx.msg = ctx.message.content.partition(' ')
        ctx.author_id = int(ctx.author.id)
        ctx.chan_as_user = channel
        # ctx.channel_copy = self.regd_channels.get(channel.id)

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
        self._built_ins = {k: v for k, v in built_in_commands.__dict__.items() if isinstance(v, Callable)}
        self.built_ins = [f.__name__ for f in self._built_ins.values() if not f.__name__.startswith('_')]
        # self._defaults = {k: v for k, v in default_commands.__dict__.items() if isinstance(v, Callable)}
        # self.defaults = [f.__name__ for f in self._defaults.values() if not f.__name__.startswith('_')]


    def _init_channels(self):
        '''Retrieves channel records from the database and initializes a
        `RegisteredChannel` object for each.'''
        records = self._db.execute("select * from channel")
        self.regd_channels = {}
        for record in records:
            channel_id = record[0]
            self.regd_channels[channel_id] = RegisteredChannel(*record)
            # self.channel_reg

    def _init_commands(self):
        '''Retrieves command records from the database and initializes a
        `RegisteredCommand` object for each.'''
        fields = _command_field_names
        _sql = f"select {','.join(fields)} from command" # where override_builtin = None"
        records = self._db.execute(_sql)
        for record in records:
            # print(f"{record=}")
            command = RegisteredCommand(*record)
            # print(self.regd_channels)
            # print(command)
            self.regd_channels[command.channel_id].commands[command.name] = command

    def register_channel(self, user_id: int, username: str, display_name: str, **vars):
        '''Registers a channel to the database if new, otherwise raises
        `RegistrationError`. This must only be called by a command invoked in
        the bot's channel.'''
        if user_id in self.regd_channels.keys():
            raise RegistrationError(f"Channel {self.regd_channels[user_id]} is already registered.")
        else:
            try:
                self.regd_channels[user_id] = RegisteredChannel(user_id, username, display_name)
                fields = ('id', 'name', 'display_name')
                _sql = f"insert into channel({','.join(fields)}) values (?,?,?)"
                with self._db_conn:
                    self._db.execute(_sql, [user_id, username, display_name])
            except sqlite3.IntegrityError as exc:
                raise RegistrationError(f"Failed registering channel {username}: {exc.args[0]}")
                # print(f"Failed registering channel {username}: {exc.args[0]}")

    def _handle_cmd(self, ctx: Context):
        '''Parses a `!cmd` string, executing `_add_command()`, `_edit_command()`
        or `_delete_command()` based on the action it implies.'''
        channel_id = ctx.chan_as_user.id
        if channel_id not in self.regd_channels:
            err = f"Channel with id {channel_id} is not registered."
            raise RegistrationError(err)
        msg = ctx.msg

        action_switch = {
            '!addcmd': 'add',
            '!editcmd': 'edit',
            '!delcmd': 'delete',
            '!disable': 'disable',
            '!enable': 'enable',
        }

        func_switch = {
            'add': self._add_command,
            'edit': self._edit_command,
            'delete': self._delete_command,
            'disable': self._edit_command,
            'enable': self._edit_command,
        }

        body = ctx.msg.split(None, 1)
        action: str = None
        if ctx.cmd == '!cmd':
            action, msg = body
            syntax = "<!cmd syntax>"
            if action not in func_switch:
                # action = body[0]
                err = f"Invalid action: {action!r}. Syntax: {syntax}"
                raise parse_cmd.InvalidAction(err)
        elif ctx.cmd in action_switch:
            action = action_switch[ctx.cmd]

        # print(f"{cmd=}")
        # print(f"{action=}")
        # print(f"{msg=}")
        # try:
        parsed = parse_cmd.parse(msg=(action + ' ' + msg))
        # except (parse_cmd.InvalidArgument, parse_cmd.InvalidSyntax, parse_cmd.InvalidAction) as exc:
            # return exc.args[0]
        # print(f"{type(parsed)=}")
        # print(f"{parsed=}")
        if isinstance(parsed, tuple):
            cmd_info, message = parsed
        elif not parsed:
            err = """Parser returned NoneType, most likely resulting from a
            --help flag. Those will be implemented soon! swifEyes"""
            raise TypeError(err)
        else:
            cmd_info = parsed
            message = None
        # channel = await ctx.channel.user()
        cmd = vars(cmd_info)
        channel_id = cmd['channel_id'] = ctx.chan_as_user.id
        cmd['name'] = cmd.get('name', [None])[0]
        # cmd.setdefault('name')
        cmd['message'] = message
        cmd['author_id'] = int(ctx.author.id)

        for k, v in tuple(cmd.items()):
            if v == None:
                del cmd[k]

        if cmd.get('aliases'):
            cmd['aliases'] = ','.join(cmd['aliases'])

        if action in action_switch.values():
            return func_switch[action](cmd)


    def _add_command(self, cmd: dict):
        '''Adds a custom command to memory and the database.'''
        error_preface = f"Unable to add command {cmd['name']!r}: "
        channel_id = cmd['channel_id']
        channel = self.regd_channels[channel_id]
        if cmd['name'] in channel.commands:
            err = f"""
            Command {cmd['name']!r} already exists! To change its
            properties, use '!cmd edit' or '!editcmd'"""
            raise RegistrationError(err)
        if cmd['name'] in self.built_ins:
            err = f"""
                Name conflict: Command name {cmd['name']!r} conflicts with
                a built-in command with the same name.
                Use '--override_builtin' if you want to replace it with your
                custom command. If you change your mind later, simply delete
                the custom command."""
            raise RegistrationError(err)

        reqd_defaults = {
        'perms': 'everyone',
        'is_hidden': 0,
        'is_enabled': 1,
        }

        for k, v in reqd_defaults.items():
            cmd.setdefault(k, v)

        command = RegisteredCommand(**cmd)
        self.regd_channels[channel_id].commands[cmd['name']] = command
        fields = command._fields
        _sql = f"insert into command({','.join(fields)}) values ({','.join(['?'] * len(fields))})"
        try:
            with self._db_conn:
                self._db.execute(_sql, command)
        except sqlite3.IntegrityError as exc:
            err = f"Failed registering command {command!r}: Database error: {exc.args[0]}"
            raise DatabaseError(error_preface + err)
        return f"Command {command.name!r} was added successfully!"


    def _edit_command(self, cmd: dict):
        '''Alters a custom command's properties in memory and the database.'''
        error_preface = f"Unable to edit command {cmd['name']!r}: "
        channel_id = cmd['channel_id']
        channel = self.regd_channels[channel_id]
        if cmd['name'] not in channel.commands:
            err = f"Command {cmd['name']!r} does not exist."
            raise RegistrationError(error_preface + err)
        if cmd['name'] in self.built_ins:
            err = f"""
                Name conflict: Command name {cmd['name']!r} conflicts with
                a built-in command with the same name.
                Use '--override_builtin' if you want to replace it with your
                custom command. If you change your mind later, simply delete
                the custom command."""
            raise RegistrationError(error_preface + err)
        if cmd['name'] not in channel.commands:
            err = f"Command {cmd['name']!r} does not exist."
            raise RegistrationError(error_preface + err)

        old_command = channel.commands[cmd['name']]._asdict()
        old_command.update(cmd)
        command = RegisteredCommand(**old_command)
        self.regd_channels[channel_id].commands[cmd['name']] = command

        try:
            columns = ','.join(command._fields)
            placeholders = ','.join(['?'] * len(command._fields))
            where = f"where (channel_id, name) = ({channel_id}, {command.name!r})"
            _sql = f"update command set({columns}) = ({placeholders}) {where}"
            with self._db_conn:
                self._db.execute(_sql, command)
        except sqlite3.Error as exc:
            # err = f"Failed registering command {command!r}: Database error: {exc.args[0]}"
            err = f"Database error: {exc.args[0]}"
            raise DatabaseError(err)
        except Exception as exc:
            print(exc.args[0])
            err = "There was an error while performing this !cmd operation:"
            return f"{err} {exc.args[0]}"
        else:
            return f"Command {command.name!r} was edited successfully!"


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