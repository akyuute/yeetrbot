# from twitchio.ext import commands
# from twitchio import channel, chatter, FollowEvent, ChannelInfo, Clip, User
# import random
# import re
# import os
import sqlite3
from db._create_tables import _create_tables
# import csv
# import atexit
# from os import environ
# from dotenv import load_dotenv
# from my_commands import string_commands

class RegistrationError(Exception): ...
class CustomError(Exception): ...

class RegisteredChannel:
    def __init__(self, user_id, username, display_name, *args, **kwargs):
        self.user_id = user_id
        self.username = username
        self.display_name = display_name
        self.built_ins = []
        self.commands = []
        self.variables = []

    def __repr__(self) -> str:
        return str(self.username)

class RegisteredCommand:
    def __init__(self, chan_id, name, aliases, message, perms, count, is_enabled):
        self.chan_id = chan_id
        self.name = name
        self.aliases = aliases
        self.message = message
        self.perms = perms
        self.count = count
        self.is_enabled = is_enabled
        # keys = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_enabled')
        # self.__dict__ = {k: v for k, v in zip(keys, self.__init__.__code__.co_varnames)}
        # print(*zip(keys, self.__init__.__code__.co_varnames))
        # print(dir(self.__init__))
        # print(self.__dict__)

    def __repr__(self) -> str:
        return str(self.name)

class RegisteredBuiltIn:
    def __init__(self, chan_id, name, aliases, perms, count, is_enabled):
        self.chan_id = chan_id
        self.name = name
        self.aliases = aliases
        self.perms = perms
        self.count = count
        self.is_enabled = is_enabled
        # keys = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_enabled')
        # self.__dict__ = {k: v for k, v in zip(keys, self.__init__.__code__.co_varnames)}
        # print(*zip(keys, self.__init__.__code__.co_varnames))
        # print(dir(self.__init__))
        # print(self.__dict__)

    def __repr__(self) -> str:
        return str(self.name)

# mycomm = RegisteredCommand('id', 'mycomm', None, 'foooo', 'everyone', 4, 1)



class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
    channel_data: dict
    def __init__(self):
        self._init_database()
        self._init_channels()
        self._init_commands()
        self._init_built_ins()

    def _init_database(self):
        self.db_conn = sqlite3.connect("db/botdb.db")
        self.db = self.db_conn.cursor()
        with self.db_conn:
            for stmt in _create_tables:
                self.db.execute(stmt)

    # def _init_channels(self):
    #     '''Retrieves registered channels from the database.'''
    #     keys = ('id', 'name', 'display_name', 'history')
    #     records = self.db.execute("select * from channel")
    #     channel_data = {}
    #     for rec in records:
    #         chan_id = int(rec[0])
    #         channel_data[chan_id] = {k: v for k, v in zip(keys, rec)} # , 'commands': {}, 'variables': {}}
    #         channel_data[chan_id]['commands'] = {}
    #         channel_data[chan_id]['variables'] = {}
    #     # print("Join:", self.db.execute("select * from channel join command on channel.id = command.chan_id").fetchall())
    #     # return channel_data
    #     self.channel_data = channel_data


    def _init_channels(self):
        fields = ('id', 'name', 'display_name', 'history')
        records = self.db.execute("select * from channel")
        # channel_data = {}
        self.regd_channels = []
        for channel in records:

            self.regd_channels.append(RegisteredChannel(*channel))
        # print([(obj.username, obj.__dict__) for obj in self.regd_channels])


    def _init_commands(self):
        fields = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_enabled')
        # records = self.db.execute("select ?,?,?,?,?,?,? from command where is_builtin = 0", fields)
        records = self.db.execute(f"select {','.join(fields)} from command where is_builtin = 0")
        commands = []
        for record in records:
            for channel in self.regd_channels:
                command = RegisteredCommand(*record)
                channel.commands.append(command)


    def _init_built_ins(self):
        fields = ('chan_id', 'name', 'aliases', 'perms', 'count', 'is_enabled')
        # records = self.db.execute("select ?,?,?,?,?,?,? from command where is_builtin = 1", fields)
        records = self.db.execute(f"select {','.join(fields)} from command where is_builtin = 0")
        built_ins = []
        for record in records:
            for channel in self.regd_channels:
                built_in = RegisteredBuiltIn(*record)
                channel.built_ins.append(built_in)

    @property
    def channels(self):
        # names += ENV['INITIAL_CHANNELS']
        return list(self.regd_channels)
        # return set(names)


    def register_channel(self, channel_user_id: int, name: str, display_name: str):
        '''Registers a new channel for the bot to serve. If the channel is
        registered, its values are updated.'''
        keys = ('id', 'name', 'display_name', 'history')
        new_dict = {k: v for k, v in zip(keys, [channel_user_id, name, display_name])}
        # self.channel_data[channel_user_id].update(new_dict)
        self.channel_data[channel_user_id] = new_dict
        _sql = "insert into channel(id, name, display_name) values (?,?,?)"
        # if channel_user_id not in self.channel_data:
        try:
            with self.db_conn:
                self.db.execute(_sql, [str(channel_user_id), name, display_name])
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])
            return exc

    def register_command(self, channel_user_id: int, command_name: str, message: str, aliases: str = None, perms: str = 'everyone', count: int = None):
        if not channel_user_id in self.channel_data:
            return RegistrationError("This channel is not registered.")
        keys = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_builtin', 'is_enabled')
        new_dict = {k: v for k, v in zip(keys, [channel_user_id, command_name, aliases, message, perms, count, 0, 1])}
        try:
            isinstance(self.channel_data[channel_user_id]['commands'], dict)
        except KeyError:
            self.channel_data[channel_user_id]['commands'] = {}
        finally:
            self.channel_data[channel_user_id]['commands'][command_name] = new_dict

        _sql = "insert into command(chan_id, name, aliases, message, perms, count, is_builtin, is_enabled) values (?,?,?,?,?,?,?,?)"
        # print([str([*new_dict.values()])])
        # if command_name not in self.channel_data[channel_user_id]['commands']:
        try:
            with self.db_conn:
                # self.db.execute(_sql, [str(channel_user_id), command_name, message, ])
                # self.db.execute(_sql, [str(v) for v in new_dict.values() if v not None])
                self.db.execute(_sql,[v for v in new_dict.values()])
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])
                # return exc

    def register_built_in(self, channel_user_id: int, command_name: str, aliases: str = None, perms: str = 'everyone', count: int = None):
        if not channel_user_id in self.channel_data:
            return RegistrationError("This channel is not registered.")
        keys = ('chan_id', 'name', 'aliases', 'perms', 'count', 'is_enabled')
        new_dict = {k: v for k, v in zip(keys, [channel_user_id, command_name, aliases, perms, count, 1])}
        try:
            isinstance(self.channel_data[channel_user_id]['commands'], dict)
        except KeyError:
            self.channel_data[channel_user_id]['commands'] = {}
        finally:
            self.channel_data[channel_user_id]['commands'][command_name] = new_dict

        _sql = "insert into command(chan_id, name, aliases, message, perms, count, is_builtin, is_enabled) values (?,?,?,?,?,?,?,?)"
        # print([str([*new_dict.values()])])
        # if command_name not in self.channel_data[channel_user_id]['commands']:
        try:
            with self.db_conn:
                # self.db.execute(_sql, [str(channel_user_id), command_name, message, ])
                # self.db.execute(_sql, [str(v) for v in new_dict.values() if v not None])
                self.db.execute(_sql,[v for v in new_dict.values()])
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])
                # return exc
        # pass

    def register_variable(self, varname: str):
        _sql = "insert into variable(var_name) values (?)"
        try:
            with self.db_conn:
                self.db.execute(_sql)
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])

    def set_chan_variable(self, varname, value):
        _sql = "update ..."
        pass


bot = Yeetrbot()
# print([channel.commands for channel in bot.regd_channels])
print([channel.__dict__ for channel in bot.regd_channels])
print(bot.channels)
print(bot.regd_channels[0].commands[1].__dict__)