# from twitchio.ext import commands
# from twitchio import channel, chatter, FollowEvent, ChannelInfo, Clip, User
# import random
# import re
# import os
import sqlite3
from db._create_tables import _create_tables
import my_commands.built_ins as built_ins
# import csv
# import atexit
# from os import environ
# from dotenv import load_dotenv


class AssignmentError(Exception): ...
class RegistrationError(AssignmentError): ...

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
        self.register_channel(123456, 'foo', 'FOO')
        # self.register_command(436164774, "testcomm", "asoidc")

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
        self.regd_channels = []
        # channel_data = {}
        # self.regd_channels_dict = {}
        for record in records:
            self.regd_channels.append(RegisteredChannel(*record))
            channel = {k: v for k, v in zip(fields, record)}
            # self.regd_channels_dict[channel['name']] = RegisteredChannel(*record)
        # print([(obj.username, obj.__dict__) for obj in self.regd_channels])


    def _init_commands(self):
        fields = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_enabled')
        # records = self.db.execute("select ?,?,?,?,?,?,? from command where is_builtin = 0", fields)
        _sql = f"select {','.join(fields)} from command where is_builtin = 0"
        records = self.db.execute(_sql)
        # commands = []
        for record in records:
            for channel in self.regd_channels:
                command = RegisteredCommand(*record)
                channel.commands.append(command)


    def _init_built_ins(self):
        fields = ('chan_id', 'name', 'aliases', 'perms', 'count', 'is_enabled')
        # records = self.db.execute("select ?,?,?,?,?,?,? from command where is_builtin = 1", fields)
        _sql = f"select {','.join(fields)} from command where is_builtin = 0"
        records = self.db.execute(_sql)
        # built_ins = []
        for record in records:
            for channel in self.regd_channels:
                built_in = RegisteredBuiltIn(*record)
                channel.built_ins.append(built_in)

    @property
    def channels(self):
        # names += ENV['INITIAL_CHANNELS']
        return list(self.regd_channels)
        # return set(names)


    # def register_channel(self, channel_user_id: int, name: str, display_name: str):
    #     '''Registers a new channel for the bot to serve. If the channel is
    #     registered, its values are updated.'''
    #     keys = ('id', 'name', 'display_name', 'history')
    #     new_dict = {k: v for k, v in zip(keys, [channel_user_id, name, display_name])}
    #     # self.channel_data[channel_user_id].update(new_dict)
    #     self.channel_data[channel_user_id] = new_dict
    #     _sql = "insert into channel(id, name, display_name) values (?,?,?)"
    #     # if channel_user_id not in self.channel_data:
    #     try:
    #         with self.db_conn:
    #             self.db.execute(_sql, [str(channel_user_id), name, display_name])
    #             self.db_conn.commit()
    #     except sqlite3.Error as exc:
    #         print(exc.args[0])
    #         return exc

    def register_channel(self, user_id: int, username: str, display_name: str, **vars):
        '''Registers a channel to regd_channels if new, otherwise raises RegistrationError.
        Assumes the command was called in the bot's channel.'''
        if user_id != [channel.user_id for channel in self.regd_channels]:
            self.regd_channels.append(RegisteredChannel(user_id, username, display_name))
            fields = ('id', 'name', 'display_name')
            _sql = f"insert into channel({','.join(fields)}) values (?,?,?)"
            self.db.execute(_sql, [user_id, username, display_name])
        else:
            raise RegistrationError(f"Channel {username} is already registered.")

    def register_command(self, channel_user_id: int, command_name: str, message: str, aliases: str = None, perms: str = 'everyone', count: int = None):
        if not channel_user_id in self.channel_data:
            return RegistrationError("This channel is not registered.")
        fields = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_builtin', 'is_enabled')
        new_dict = {k: v for k, v in zip(fields, [channel_user_id, command_name, aliases, message, perms, count, 0, 1])}
        try:
            isinstance(self.channel_data[channel_user_id]['commands'], dict)
        except KeyError:
            self.channel_data[channel_user_id]['commands'] = {}
        finally:
            self.channel_data[channel_user_id]['commands'][command_name] = new_dict

        # _sql = "insert into command(chan_id, name, aliases, message, perms, count, is_builtin, is_enabled) values (?,?,?,?,?,?,?,?)"
        _sql = f"insert into command({','.join(fields)}) values (?,?,?,?,?,?,?,?)"
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

    def register_command(self, channel_id: int, command_name: str, message: str, aliases: str = None, perms: str = 'everyone', count: int = None):
        '''Registers a custom command to regd_channels if the channel exists,
        otherwise raises RegistrationError. Assumes moderator permissions.'''
        if channel_id != [channel.user_id for channel in self.regd_channels][0]:
            raise RegistrationError(f"Channel {channel_id} is not registered.")
        # print(*[channel.commands for channel in self.regd_channels if channel.user_id == channel_id])
        channel_commands = [channel.commands for channel in self.regd_channels if channel.user_id == channel_id][0]
        if command_name in [command.name for command in channel_commands]:
            raise AssignmentError(f"Command name {command_name!r} overwrites a command with the same name.")
        if command_name in built_ins.__dict__:
            raise AssignmentError(f"Command name {command_name!r} overwrites a built-in command with the same name.")

        pass


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
# print(bot.regd_channels[0].commands[1].__dict__)
# print(bot.regd_channels_dict)
print([channel.commands for channel in bot.regd_channels])


# bot.db_conn.commit()