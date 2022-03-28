# from twitchio.ext import commands
# from twitchio import channel, chatter, FollowEvent, ChannelInfo, Clip, User
# import random
# import re
# import os
from collections import namedtuple
import sqlite3
from typing import Callable, Sequence
from db._create_tables import _create_tables
import my_commands.built_ins as built_in_commands
import my_commands.default_commands as default_commands
# import csv
# import atexit
# from os import environ
# from dotenv import load_dotenv
import parse_cmd


class AssignmentError(Exception): ...
class RegistrationError(AssignmentError): ...

class RegisteredChannel:
    def __init__(self, user_id: int, username: str, display_name: str, *args, **kwargs):
        self.user_id = user_id
        self.username = username
        self.display_name = display_name
        self.built_ins = {}
        self.commands = {}
        self.variables = {}

        # self._repr = f"{self.__class__}" 
        # self._repr = f"<RegisteredChannel({user_id=}, {username=})>"
        self._repr = f"<RegisteredChannel({username=})>"

    def __repr__(self) -> str:
        return self._repr
        # return str(self.username)

# class RegisteredCommand:
#     def __init__(self, channel_id: int, name: str, values: dict):
#         self.__dict__ = values
#         self.channel_id = channel_id
#         self.name = name
#         perms = values['perms']
#     # def __init__(self, channel_id: int, name: str, message: str|None,
#     #     aliases: Sequence|str|None, perms: str, count: int, is_hidden: int, override_builtin: int, is_enabled: int, author_id:str):
#     #     self.channel_id = channel_id
#     #     self.name = name
#     #     self.message = message
#     #     self.aliases = aliases
#     #     self.perms = perms
#     #     self.count = count
#     #     self.is_hidden = is_hidden
#     #     self.override_builtin = override_builtin
#     #     self.is_enabled = is_enabled
#     #     self.author_id = author_id

#         # self._repr = str(self.__class__)
#         self._repr = f"<RegisteredCommand({name=}, {perms=}, {channel_id=})>"

#     def __repr__(self) -> str:
#         return self._repr
#     #     return str(self.name)

command_field_names = '''channel_id name message aliases perms count is_hidden
    override_builtin is_enabled author_id modified_by modified_on ctime mtime'''.split()

RegisteredCommand = namedtuple('RegisteredCommand', command_field_names,
    defaults=[None] * (len(command_field_names) - 2))
# class RegisteredCommand(namedtuple('RegisteredCommand', **_registered_command_, defaults=[None]*len(_registered_command_['field_names']))):
#     def __repr__(self) -> str:
#         return ''


class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
    channel_data: dict
    def __init__(self):
        self._init_database()
        self._init_channels()
        self._init_commands()
        # self._init_built_ins()

        # self.register_channel(3141, 'dy', 'D_Y')
        # self.update_command(3141, "uwu", "asoidc", perms="moderator")
        # self.update_command(3141, "uptime", "asoidc", perms="moderator")
        # self.update_command(3141, "adivjn", "asoidc", perms="moderator")
        # self.register_channel(59873, 'asdoci', 'BAR')
        # self.update_command(59873, 'mycomm', 'mymsg')
        # self.update_command(193457, "adivjn", "asoidc")
        # self._update_command(3141, 'testadd', 'foo', None, None, None, None, None, 'add')
        # self._update_command(3141, 'testadd', 'bar', "None", None, None, None, 0, 'edit')

    @property
    def channels(self):
        '''A list of registered channel names.'''
        # names += ENV['INITIAL_CHANNELS']
        return [c.username for c in self.regd_channels.values()]

    def _init_database(self):
        '''Connects to the sqlite3 database and creates tables if necessary.'''
        self._db_conn = sqlite3.connect("db/botdb.db")
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

    def _init_commands(self):
        '''Retrieves command records from the database and initializes a
        `RegisteredCommand` object for each.'''
        # fields = ('channel_id', 'name', 'aliases', 'message', 'perms', 'count', 'override_builtin', 'is_enabled')
        fields = '''channel_id name message aliases perms count is_hidden
            override_builtin is_enabled author_id modified_by modified_on ctime mtime'''.split()
        _sql = f"select {','.join(fields)} from command" # where override_builtin = None"
        records = self._db.execute(_sql)
        for record in records:
            print(f"{record=}")
            command = RegisteredCommand(*record)
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


    # def parse_commands_str(self, cmd: str, msg: str):
    #     args = msg.split(' ')
    #     out = None
    #     name = message = aliases = perms = count = override_builtin = is_enabled = None
    #     try:
    #         args.insert(0, cmd_switch[args[0]])
    #     except KeyError as exc:
    #         print(exc.args[0])
    #     if args
    #     thing = vars(parse_cmd.parse(' '.join(args)))


    #     pass


    # def _insert_new_command(self, channel_id: int, command_name: str, message: str|None, aliases: Sequence|str|None, perms: str, count: int, is_hidden: int, override_builtin: int, is_enabled: int):
    #     '''Called by `update_command()`. Commits a new command to the database.'''
    #     fields = ('channel_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_hidden', 'override_builtin', 'is_enabled')
    #     _sql = f"insert into command({','.join(fields)}) values ({','.join(['?'] * len(fields))})"
    #     vals = (channel_id, command_name, message, aliases, perms, count, is_hidden, override_builtin, is_enabled)
    #     try:
    #         with self._db_conn:
    #             self._db.execute(_sql, vals)
    #     except sqlite3.IntegrityError as exc:
    #         raise RegistrationError(f"Failed registering command {command_name}: {exc.args[0]}")
    #         # print(f"Failed registering command {channel_commands[command_name]}: {exc.args[0]}")

    # def _update_command(self, values: dict):
    # # def _update_command(self, channel_id: int, command_name: str, message: str|None, aliases: Sequence|str|None, perms: str, count: int, is_hidden: int, override_builtin: int, is_enabled: int):
        # '''Called by `update_command()`. Commits a new command to the database.'''
        #fields = ('channel_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_hidden', 'override_builtin', 'is_enabled')
        #vals = tuple(v for v in vals.values())
        #vals = (channel_id, command_name, message, aliases, perms, count, is_hidden, override_builtin, is_enabled)
        #_sql = f"update command set({','.join(fields)}) values ({','.join(['?'] * len(fields))}) where (channel_id, name) = ({vals['channel_id']}, {vals['name']})"

        # fields, vals = ((i[0], i[1]) for i in values.items())
        # _sql = f"update command set({','.join(fields)}) values ({','.join(['?'] * len(fields))}) where (channel_id, name) = ({values['channel_id']}, {values['name']})"
        # try:
        #     with self._db_conn:
        #         self._db.execute(_sql, vals)
        # except sqlite3.IntegrityError as exc:
        #     raise RegistrationError(f"Failed registering command {command_name}: {exc.args[0]}")
        #     # print(f"Failed registering command {channel_commands[command_name]}: {exc.args[0]}")


    # def update_command(self, channel_id: int, action: str, command_name: str, message: str|None, aliases: Sequence|str|None, perms: str, count: int, is_hidden: int, override_builtin: int, is_enabled: int, new_name: str):
    def _update_command(self, action, cmd_info: dict, ):
        '''Registers a custom command to the database if the command name is
        unused if the channel exists. Otherwise raises `RegistrationError`.
        Assumes moderator permissions.'''

        channel_id = cmd_info['channel_id']
        command_name = cmd_info['name'][0]
        if channel_id not in self.regd_channels.keys():
            raise RegistrationError(f"Channel with id {channel_id} is not registered.")
        channel_commands = self.regd_channels[channel_id].commands
        print(f"{type(channel_commands)}")
        if command_name in self.built_ins:
            raise RegistrationError(f"Command name {command_name!r} conflicts with a built-in command with the same name.")
        # if command_name in self.defaults:
        #     raise RegistrationError(f"Command name {command_name!r} conflicts with a default command with the same name.")

        for k, v in tuple(cmd_info.items()):
            if v == None:
                del cmd_info[k]

        cmd_info.update(channel_id=channel_id)
        cmd_info.update(name=command_name)
        if cmd_info.get('aliases'):
            cmd_info.update(aliases=','.join(cmd_info['aliases']))
        command_info = RegisteredCommand(**cmd_info)

        if action == 'add':
            if command_name in channel_commands.keys():
                raise RegistrationError(f"{channel_commands[command_name]} is already registered.")
            command_info = command_info._replace(is_hidden=0, override_builtin=0, is_enabled=1)
            self.regd_channels[channel_id].commands[command_name] = command_info
            # self.regd_channels[channel_id].commands[command_name] = 
            # fields = cmd_info.keys()
            # vals = cmd_info.values()
            fields = command_info._fields
            _sql = f"insert into command({','.join(fields)}) values ({','.join(['?'] * len(fields))})"
            try:
                with self._db_conn:
                    self._db.execute(_sql, command_info)
            except sqlite3.IntegrityError as exc:
                raise RegistrationError(f"Failed registering command {command_name}: {exc.args[0]}")
            return f"Command {command_name} successfully added."

        elif action == 'edit':
            if command_name not in channel_commands.keys():
                raise RegistrationError(f"Command name {command_name} has not been registered.")
            # update_dict = dict(*(i for i in cmd_info.items() if i[1] != None))
            # fields, vals = ((i[0], i[1]) for i in update_dict.items())

            old_command = self.regd_channels[channel_id].commands[command_name]
            # print(f"{type(old_command._asdict())=}")
            old_command._asdict().update(cmd_info)
            new_command = RegisteredCommand(**old_command._asdict())
            self.regd_channels[channel_id].commands[command_name] = new_command
            fields = new_command._fields
            # self.regd_channels[channel_id].commands[command_name].__dict__.update(fields)

            try:
                _sql = f"update command set({','.join(fields)}) values ({','.join(['?'] * len(fields))}) where (channel_id, name) = ({str(channel_id)}, {command_name})"
                with self._db_conn:
                    self._db.execute(_sql, new_command)
            except sqlite3.IntegrityError as exc:
                raise RegistrationError(f"Failed registering command {command_name}: {exc.args[0]}")
            return f"Command {command_name} successfully edited."



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
    print([channel.__dict__ for channel in bot.regd_channels.values()])
    # print([command.__dict__ for command in bot.regd_channels[3141].commands])
    print([comm.message for comm in bot.regd_channels[3141].commands.values()])
    # print(bot.regd_channels)
    # print(bot.channels)
    # print(bot.regd_channels[0].commands[1].__dict__)
    # print(bot.regd_channels[436164774].commands)
    # print([channel.commands for channel in bot.regd_channels])
    # print(bot.regd_channels.get(436164774).commands)


# bot._db_conn.commit()