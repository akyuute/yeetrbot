# from twitchio.ext import commands
from twitchio.ext.commands import Context
import re
# import os
import time
import random
import sqlite3
# import atexit
from textwrap import dedent
#from collections import namedtuple
import dataclasses as dc
from dataclasses import dataclass, astuple, asdict

import my_commands.built_ins as built_in_commands
# import my_commands.default_commands as default_commands
from my_commands import string_commands
from parsing import parse_cmd
from errors import *
from typing import Callable, Sequence


_db_file = "db/bot.db"


@dataclass # (slots=True)
class RegisteredCommand:
    channel_id: int
    name: str
    message: str = dc.field(repr=False)
    aliases: list[str] = []
    perms: str = 'everyone'
    count: int = 0
    is_hidden: bool = dc.field(default=False)
    is_enabled: bool = dc.field(default=True)
    author_id: int = dc.field(repr=False)
    author_name: str = dc.field(repr=False)
    modified_by: str = dc.field(repr=False)
    # Times in seconds since epoch; use time.gmtime() to convert to UTC
    ctime: int = dc.field(repr=False)
    mtime: int = dc.field(repr=False)
    override_builtin: bool = dc.field(default=None, repr=False)


@dataclass(slots=True)
class RegisteredChannel:
    channel_id: int
    username: str
    display_name: str
    commands: dict = {}


class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
    def __init__(self):
        self._init_database(_db_file)
        self._init_channels()
        self._init_commands()
        # self._init_built_ins()

    def _init_database(self, db_file: str):
        '''Connects to the sqlite3 database and creates tables if necessary.'''
        self._db_conn = sqlite3.connect(db_file)
        self._db = self._db_conn.cursor()
        with self._db_conn:
            with open('db/schema.sql', 'r') as f:
                self._db.executescript(f.read())
            #for stmt in _create_tables:
                #self._db.execute(stmt)
        self._built_ins = {k: v for k, v in built_in_commands.__dict__.items()
                           if isinstance(v, Callable)}
        self.built_ins = [f.__name__ for f in self._built_ins.values()
                          if not f.__name__.startswith('_')]
        # self._defaults = {k: v for k, v in default_commands.__dict__.items()
        #                   if isinstance(v, Callable)}
        # self.defaults = [f.__name__ for f in self._defaults.values()
        #                  if not f.__name__.startswith('_')]

    def _init_channels(self):
        '''Retrieves channel records from the database and
        initializes a `RegisteredChannel` object for each.'''
        records = self._db.execute("select * from channel")
        self._registry = {}
        for record in records:
            channel_id = record[0]
            self._registry[channel_id] = RegisteredChannel(*record)

    @property
    def channels(self):
        '''A list of registered channel names.'''
        # names += ENV['INITIAL_CHANNELS']
        return [c.username for c in self._registry.values()]

    def _init_commands(self):
        '''Retrieves command records from the database and
        initializes a `RegisteredCommand` object for each.'''
        fields = ','.join(_command_field_names)
        # cond = "where override_builtin = None"
        cond = ""
        _sql = f"select {fields} from command {cond}"
        records = self._db.execute(_sql)
        for record in records:
            cmd = RegisteredCommand(*record)
            self._registry[cmd.channel_id].commands[cmd.name] = cmd
 
    # def get_commands(self, channel_id: int):
        # return [c.name for c in self._registry[channel_id].commands]


    def _register_channel(self, uid: int, name: str, display_name: str):
        '''Registers a channel to the database if new, otherwise raises
        `RegistrationError`. This must only be called by a command sent
        in the bot's channel.'''
        if uid in self._registry:
            err = f"Channel {name!r} is already registered."
            raise RegistrationError(err)
        channel = RegisteredChannel(uid, name, display_name)
        self._registry[uid] = channel
        fields = ('id', 'name', 'display_name')
        _sql = f"insert into channel({','.join(fields)}) values (?,?,?)"
        try:
            with self._db_conn:
                self._db.execute(_sql, astuple(channel))
        except sqlite3.Error as exc:
            raise DatabaseError(exc.args[0])

    def _join_channel(self, ctx: Context):
        '''Registers a new channel to the database when invoked within
        the bot's Twitch channel and returns the response to be sent.'''
        resp = ""
        username = ctx.author.name
        display_name = ctx.author.display_name
        error_preface = f"Failed registering channel {name!r}"

        if ctx.author_id not in self._registry:
            try:
                self._register_channel(ctx.author_id, username, display_name)
                resp = "I've successfully joined your channel. See you there!"
                print(f"Registered new channel {display_name}")
                print(self._registry)
            except RegistrationError as exc:
                err = f"{error_preface}: Registration error: {exc.args[0]}"
                raise RegistrationError(err)
            except DatabaseError as exc:
                err = f"{error_preface}: Database error: {exc.args[0]}"
                raise DatabaseError(err)
        else:
            resp = "I am already in your channel!"
        return resp

    def _manage_custom_command(self, ctx: Context, base_name: str = 'cmd',
            alias_names="addcmd editcmd delcmd disable enable alias".split()):
        '''Parses a `!cmd` string and executes `_add_command()`,
        `_edit_command()` or `_delete_command()` based on the implied action.
        '''
        channel_id = ctx.chan_as_user.id
        if channel_id not in self._registry:
            err = f"Channel with id {channel_id} is not registered."
            raise ChannelNotFoundError(err)

        # alias_names="addcmd editcmd delcmd disable enable alias".split()
        actions = "add edit delete disable enable alias".split()
        action_switch = dict(zip(alias_names, actions))

        func_switch = {
            'add': self._add_command,
            'edit': self._edit_command,
            'delete': self._delete_command,
            'disable': self._toggle_command,
            'enable': self._toggle_command,
            'alias': self._edit_command
        }

        test_prefixes = {ctx.cmd.removeprefix(p) for p in ctx.prefix}
        prefixless = (lambda x: x[min(x)])({len(c): c for c in test_prefixes})
        action = ''
        msg = ctx.msg
        body = ctx.msg.split(None, 1)
        # if len(body) != 2:
            # try:
                # return parsing(body[0])
            # except Exception as exc:
                # print("Parser exception...", exc)
                # print(type(exc), exc.args[0])
        if prefixless == base_name:
            action, msg = body
            syntax = "<cmd syntax>"
            if action not in func_switch:
                err = f"Invalid action: {action!r}. Syntax: {syntax}"
                raise InvalidAction(err)
        elif prefixless in action_switch:
            action = action_switch[prefixless]

        parsed = parsing(msg=f"{action} {msg}")
        # print("Parsed:", parsed)

        if isinstance(parsed, tuple):
            cmd_dict = vars(parsed[0])
            message = parsed[1]
        elif parsed is None:
            err = """
                Failed to perform requested operation:
                Parser returned NoneType, most likely resulting
                from a --help flag. Those will be implemented soon!"""
            raise NotImplementedError(err)
        else:
            cmd_dict = vars(parsed)
            message = None

        used_alias = prefixless in action_switch
        cmd_dict['message'] = message
        cmd_dict['author_id'] = author_id
        cmd_dict['used_alias'] = used_alias

        if action == 'add':
            cmd = RegisteredCommand(**{k: v for k, v in cmd_dict if v is not None})
            cmd.last_action = action
            cmd.used_alias = used_alias
            return func_switch[action](cmd)
        elif action in action_switch.values():
            return func_switch[action](cmd_dict)

    def _add_command(self, cmd: RegisteredCommand):
        '''Adds a custom command to memory and the database.'''
        name = cmd.name
        action = cmd.last_action
        channel_id = cmd.channel_id
        commands = self._registry[channel_id].commands
        used_shortcut = cmd.used_shortcut
        error_preface = f"Failed to register command {cmd.name!r}"
        err = ""

        if name in commands:
            err = f"""
                {error_preface}:
                This command already exists. To change its message or
                properties, use {('!cmd edit', '!editcmd')[used_alias]!r}."""
            # Use '!cmd add -h' for details.
            # You can rename it with '!editcmd <oldname> --rename <newname>'.
            # To delete it completely, use '!delcmd'."""
        elif name in self.built_ins:
            err = f"""
                {error_preface}:
                Command name conflicts with a built-in command with the same
                name. Use '--override_builtin' if you want to replace it with
                your custom command. If you change your mind later, simply
                delete the custom command."""
        elif cmd.message is None:
            err = """
                {error_preface}:
                A message is required when adding a new command.
                Messages must come after any arguments."""
        if err:
            raise RegistrationError(err)

        self._registry[channel_id].commands[name] = cmd
        # fields = dc.fields(cmd))
        # cols = ','.join(fields)
        # vals = ','.join(['?'] * len(fields))
        # plchd = (':' + v for v in dc.asdict(cmd).values())
        cols, vals = dc.asdict(cmd).items()
        plchd = ','.join(':' + v for v in vals)
        _sql = f"insert into command({cols}) values ({plchd})"
        try:
            with self._db_conn:
                self._db.execute(_sql, vals)
        except sqlite3.Error as exc:
            err = f"{error_preface}: DatabaseError: {exc.args[0]}"
            raise DatabaseError(err)
        print("Added:", cmd)
        return f"Successfully added command {name!r}."

    def _edit_command(self, cmd: dict):
        '''Alters a custom command's properties in memory and the database.'''
        channel_id = cmd['channel_id']
        commands = self._registry[channel_id].commands
        name = cmd.get('name')
        new_name = cmd.get('new_name')
        action = cmd.get('action')
        used_shortcut = cmd.get('used_shortcut')
        unstored = 'new_name', 'action', 'used_shortcut'
        # del cmd['action'], cmd['used_shortcut']
        error_preface = f"Falied to update command {name!r}"
        err = ""

        if name not in commands and name is not None:
            raise CommandNotFoundError("""
                {error_preface}: This command does not exist.
                Use '!addcmd' to add it.""")
        elif new_name in commands:
            raise NameConflict(f"""
                {error_preface}: Naming conflict: The name {new_name!r}
                matches another command with the same name.
                Please find a different new name for {name!r}.""")
        elif new_name in self.built_ins and not override_builtin:
            raise NameConflict(f"""
                {error_preface}: Naming conflict: The name {new_name!r}
                matches a built-in command with the same name.
                Use '--override_builtin' if you want to replace it
                with your custom command. If you change your mind later,
                simply delete the custom command.""")
        
        cmd['name'] = new_name or name
        for attr, val in cmd.items():
            if val not in unstored and val is not None:
                setattr(self._registry[channel_id].commands[name], attr, val)

        keys, vals = zip(*dc.asdict(cmd).items())
        cols = ','.join(keys)
        params = ','.join(['?'] * len(command._fields))
        cond = f"(channel_id, name) = ({channel_id}, {name!r})"
        _sql = f"update command set({cols}) = ({params}) where {cond}"

        try:
            with self._db_conn:
                self._db.execute(_sql, vals)
        except sqlite3.Error as exc:
            err = f"{error_preface}: Database error: {exc.args[0]}"
            raise DatabaseError(err)
        # except Exception as exc:
            # err = """
                # An unexpected error occurred while attempting this operation: 
                # {exc.args[0]}"""
            # raise err
        print("Edited:", command)
        return f"Successfully updated command {name!r}."


    def _toggle_command(self, cmd: dict):
        '''Disable or enable a command by updating
        the database and in-memory dc.'''
        channel_id = cmd['channel_id']
        commands = self._registry[channel_id].commands
        names = set(cmd.get('commands'))
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to {action} command{plur}"

        action = cmd.get('action')
        actions = ('disable', 'enable')
        if action not in actions:
            err = f"""
                Failed to perform the requested operation:
                Invalid action: {action!r}"""
            raise InvalidAction(err)

        attr = 'is_enabled'
        toggle = action == 'enable'
        for name in names:
            if name not in self._registry[channel_id].commands:
                err = f"{error_preface}: Command {name!r} does not exist."
                raise CommandNotFoundError(err)
            self._registry[channel_id].commands[name].is_enabled = toggle

        cond = f"(channel_id, name) = ({channel_id}, ?)"
        _sql = f"update command set is_enabled = ? where {cond}"
        try:
            with self._db_conn:
                self._db.executemany(_sql, zip(toggles, names))
        except sqlite3.Error as exc:
            err = f"{error_preface}: Database error: exc.args[0]"
            raise DatabaseError(err)

        desc = f"{count} command{plur}" if plur else f"command {names[0]!r}"
        resp = f"Successfully {action}d {desc}."
        return resp


    def _delete_command(self, cmd):
        '''Delete a command, update the database and in-memory dataclass.'''
        channel_id = cmd['channel_id']
        names = set(cmd.get('commands'))
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to delete {len(names)} command{plur}"
        err = ""

        for name in names:
            if name in self._registry[channel_id].commands:
                del self._registry[channel_id].commands[name]
            elif name in self.built_ins:
                err = f"""
                    {error_preface}: Command {name!r} is a built-in command.
                    It cannot be deleted, but you may disable
                    it with '!disable {name}'."""
                raise NameConflict(err)
            else:
                err = f"{error_preface}: Command {name!r} does not exist."
                raise CommandNotFoundError(err)

        cond = f"(channel_id, name) = ({channel_id}, ?)"
        _sql = f"delete from command where {cond}"
        try:
            with self._db_conn:
                self._db.executemany(_sql, names)
        except sqlite3.Error as exc:
            err = f"{error_preface}: Database error: {exc.args[0]}"
            raise DatabaseError(error_preface + err)
        except Exception as exc:
            err = "An unexpected error occurred while attempting this operation: "
            return error_preface + err + exc.args[0]
        desc = f"{count} command{plur}" if plur else f"command {names.pop()!r}"
        resp = f"Successfully deleted {desc}."
        return resp

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
    # print([channel.commands for channel in bot._registry])
    # print([channel.__dict__ for channel in bot._registry])
    # print([channel.__dict__ for channel in bot._registry.values()])
    # print(bot._registry)
    # print(bot.channels)
    # print(bot._registry[0].commands[1].__dict__)
    # print([channel.commands for channel in bot._registry])

    # bot._db_conn.commit()
