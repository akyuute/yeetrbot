# from twitchio.ext import commands
from twitchio.ext.commands import Context
import random
import re
import time
# import os
# import atexit

#from collections import namedtuple
import dataclasses
from dataclasses import dataclass, fields, astuple, asdict
from typing import Callable, Sequence

import sqlite3
from textwrap import dedent
import my_commands.built_ins as built_in_commands
# import my_commands.default_commands as default_commands
from my_commands import string_commands
import parse_cmd


_db_file = "db/bot.db"


class AssignmentError(Exception): ...
class RegistrationError(AssignmentError): ...
class DatabaseError(Exception): ...


@dataclass # (slots=True)
class RegisteredCommand:
    channel_id: int
    name: str
    message: str = dataclasses.field(repr=False)
    aliases: list[str] = []
    perms: str = 'everyone'
    count: int = 0
    is_hidden: bool = dataclasses.field(default=False)
    is_enabled: bool = dataclasses.field(default=True)
    author_id: int = dataclasses.field(repr=False)
    author_name: str = dataclasses.field(repr=False)
    modified_by: str = dataclasses.field(repr=False)
    # Times in seconds since epoch; use time.gmtime() to convert to UTC
    ctime: int = dataclasses.field(repr=False)
    mtime: int = dataclasses.field(repr=False)
    override_builtin: bool = field(default=None, repr=False)


@dataclass(slots=True)
class RegisteredChannel:
    channel_id: int
    username: str
    display_name: str
    commands: RegisteredCommand


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
        '''Retrieves channel records from the database and initializes a
        `RegisteredChannel` object for each.'''
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
        '''Retrieves command records from the database and initializes a
        `RegisteredCommand` object for each.'''
        fields = ','.join(_command_field_names)
        # cond = "where override_builtin = None"
        cond = ""
        _sql = f"select {fields} from command {cond}"
        records = self._db.execute(_sql)
        for record in records:
            cmd = RegisteredCommand(*record)
            self._registry[cmd.channel_id].commands[cmd.name] = cmd

    def _join_channel(self, ctx: Context):
        '''Registers a new channel and adds it to the IRC bot's list of joined
        channels when invoked within the bot's Twitch channel, then returns the
        response and username for `commands.Bot.join_channels()`.'''
        resp = ""
        username = ctx.author.name
        display_name = ctx.author.display_name
        if ctx.author_id not in self._registry:
            try:
                # First, enter the channel into the database and memory:
                self._register_channel(ctx.author_id, username, display_name)
                # Then, add the channel to the IRC bot's joined channels list:
                resp = "I've successfully joined your channel. See you there!"
                print(f"Registered new channel {display_name}")
                print(self._registry)
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

    def _register_channel(self, uid: int, name: str, display_name: str):
        '''Registers a channel to the database if new, otherwise raises
        `RegistrationError`. This must only be called by a command invoked in
        the bot's channel.'''
        if uid in self._registry:
            err = f"Channel {name} is already registered."
            raise RegistrationError(err)
        channel = RegisteredChannel(uid, name, display_name)
        self._registry[uid] = channel
        fields = 'id', 'name', 'display_name'
        _sql = f"insert into channel({','.join(fields)}) values (?,?,?)"
        try:
            with self._db_conn:
                self._db.execute(_sql, astuple(channel))
        except sqlite3.Error as exc:
            err = f"Failed registering channel {name!r}: {exc.args[0]}"
            raise DatabaseError(err)

    def _manage_custom_command(self, ctx: Context, built_in_name: str = 'cmd'):
        '''Parses a `!cmd` string and executes `_add_command()`,
        `_edit_command()` or `_delete_command()` based on the implied action.
        '''
        chnlid = ctx.chan_as_user.id
        if chnid not in self._registry:
            err = f"Channel with id {chnid} is not registered."
            raise RegistrationError(err)

        action_switch = {a + built_in_name: a for a in 'add edit del'.split()}
        action_switch.update({a: a for a in 'disable, enable, alias'.split()})
        action_switch['del' + built_in_name] = 'delete'

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
                # return parse_cmd.parse(body[0])
            # except Exception as exc:
                # print("Parser exception...", exc)
                # print(type(exc), exc.args[0])
        if prefixless == built_in_name:
            action, msg = body
            syntax = "<cmd syntax>"
            if action not in func_switch:
                err = f"Syntax error: Invalid action: {action!r}. Syntax: {syntax}"
                raise parse_cmd.InvalidAction(err)
        elif prefixless in action_switch:
            action = action_switch[prefixless]

        parsed = parse_cmd.parse(msg=f"{action} {msg}")
        # print("Parsed:", parsed)

        if isinstance(parsed, tuple):
            cmd_dict = vars(parsed[0])
            message = parsed[1]
        elif parsed is None:
            err = """
            Parser returned NoneType, most likely resulting from a
            --help flag. Those will be implemented soon!"""
            raise NotImplementedError(err)
        else:
            cmd_dict = vars(parsed)
            message = None

        cmd_dict['message'] = message
        cmd_dict['author_id'] = author_id

        cmd = RegisteredCommand(**{k: v for k, v in cmd_dict if v is not None})
        cmd.last_action = action
        cmd.used_shortcut = used_shortcut
        new_name = cmd_dict.get('new_name')
        cmd.new_name = new_name

        if action in action_switch.values():
            return func_switch[action](cmd)

    def _add_command(self, cmd: RegisteredCommand):
        '''Adds a custom command to memory and the database.'''
        channel_id = cmd.channel_id
        action = cmd.last_action
        name = cmd.name
        commands = self._registry[channel_id].commands
        used_shortcut = cmd.used_shortcut
        error_preface = f"Failed to register command {cmd.name!r}: "
        err = ""

        if name in commands:
            err = f"""
            Command already exists.
            To change its message or properties, use
            {('!cmd edit', '!editcmd')[used_shortcut]!r}.
            """
            # Use '!cmd add -h' for details.
            # You can rename it with '!editcmd <oldname> --rename <newname>'.
            # To delete it completely, use '!delcmd'."""
        elif name in self.built_ins:
            err = f"""
            Command name conflicts with a built-in command with the same name.
            Use '--override_builtin' if you want to replace it with your custom
            command. If you change your mind later,
            simply delete the custom command."""
        elif cmd.message is None:
            err = """
            A message is required when adding a new command.
            Messages come after any arguments."""
        if err:
            raise RegistrationError(error_preface + dedent(err))

        self._registry[channel_id].commands[name] = cmd
        fields = ','.join(fields(cmd))
        vals = ','.join(['?'] * len(fields(cmd)))
        _sql = f"insert into command({fields}) values ({vals})"
        try:
            with self._db_conn:
                self._db.execute(_sql, astuple(cmd))
        except sqlite3.Error as exc:
            err = f"DatabaseError: "
            raise DatabaseError(error_preface + err + exc.args[0])
        print("Added:", cmd)
        return f"Successfully added command {name!r}."

    def _edit_command(self, cmd: RegisteredCommand):
        '''Alters a custom command's properties in memory and the database.'''
        channel_id = cmd.channel_id
        action = cmd.last_action
        name = cmd.name
        new_name = cmd.new_name
        used_shortcut = cmd.used_shortcut
        commands = self._registry[channel_id].commands
        error_preface = f"Falied to update command {name!r}: "
        err = ""

        if name not in commands and name is not None:
            err = "This command does not exist. Use '!addcmd' to add it."
        elif new_name in commands:
            err = f"""
            Naming conflict: The name {new_name!r} matches another command with
            the same name. Please find a different new name for {name!r}."""
        elif new_name in self.built_ins and not override_builtin:
            err = f"""
            Naming conflict: The name {new_name!r} matches a built-in command
            with the same name. Use '--override_builtin' if you want to replace
            it with your custom command. If you change your mind later, simply
            delete the custom command."""
        if err:
            raise RegistrationError(error_preface + dedent(err))
        
        store_as = name or new_name
        old_command = commands[name]._replace(**cmd)
        if new_name:
            store_as = cmd['name'] = new_name
            del cmd['new_name']
            del self._registry[channel_id].commands[name]
        else:
            store_as = name

        self._registry[channel_id].commands[name] = command

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
        except Exception as exc:
            err = "An unexpected error occurred while attempting this operation: "
            return err + exc.args[0]
        print("Edited:", command)
        return f"Successfully updated command {name!r}."


    def _toggle_command(self, cmd: dict):
        '''Disable or enable a command by updating
        the database and in-memory dataclasses.'''
        channel_id = cmd['channel_id']
        commands = self._registry[channel_id].commands
        names = cmd.get('commands')
        count = len(names)
        plur = "s" if count > 1 else ""

        action = cmd.get('action')
        actions = ('disable', 'enable')
        if action not in actions:
            err = f"Failed to perform operation: Invalid action: {action!r}"
            raise parse_cmd.InvalidAction(err)
        error_preface = f"Failed to {action} command{plur}: "

        toggles = []
        for name in names:
            if name in commands:
                toggle = actions.index(action)
                old_command = commands[name]
                command = old_command._replace(is_enabled=toggle)
                self._registry[channel_id].commands[name] = command
                toggles.append(toggle)
            else:
                err = f"Command {name!r} does not exist."
                raise LookupError(error_preface + err)

            pairs = [(channel_id, n) for n in names]
            cond = "(channel_id, name) = (?, ?)"
            _sql = f"update command set (is_enabled) = {toggle} where {cond}"
            try:
                with self._db_conn:
                    self._db.executemany(_sql, pairs)
            except sqlite3.Error as exc:
                err = "Database error: "
                raise DatabaseError(error_preface + err + exc.args[0])
        desc = f"{count} command{plur}" if plur else f"command {names[0]!r}"
        resp = f"Successfully {action}d {desc}."
        return resp


    def _delete_command(self, cmd):
        '''Delete a command, update the database and in-memory dataclasses.'''
        print(cmd)
        channel_id = cmd['channel_id']
        names = set(cmd.get('commands'))
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to delete {len(names)} command{plur}: "
        err = ''

        for name in names:
            if name in self._registry[channel_id].commands:
                del self._registry[channel_id].commands[name]
            elif name in self.built_ins:
                err = f"""
                Command {name!r} is a built-in command. It cannot be deleted,
                but you may disable it with '!disable {name}'."""
            else:
                err = f"Command {name!r} does not exist."
            if err:
                raise LookupError(error_preface + dedent(err))

        pairs = [(channel_id, n) for n in names]
        _sql = "delete from command where (channel_id, name) = (?, ?)"
        try:
            with self._db_conn:
                self._db.executemany(_sql, pairs)
        except sqlite3.Error as exc:
            err = f"Database error: {exc.args[0]}"
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
