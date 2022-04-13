from twitchio.ext.commands import Context
import re
import sys
import time
import random
import sqlite3
import itertools
import dataclasses as dc
from textwrap import dedent
from argparse import ArgumentParser
from configparser import ConfigParser

import my_commands.built_ins as built_in_commands
# import my_commands.default_commands as default_commands
from my_commands import string_commands
from parsing import parse_cmd, fuzzy_split
from errors import *
from typing import Callable, Sequence


class Config(ConfigParser):
    def __init__(self, file):
        cli_parser = ArgumentParser()
        cli_parser.add_argument('--config')

        super().__init__(empty_lines_in_values=False)
        config_file = cli_parser.parse_args(sys.argv[1:]).config or file
        with open(config_file, 'r') as f:
            self.read_file(f)
        self.file = file

        nested_attrs = (self.items(sec) for sec in self)
        pairs = itertools.chain.from_iterable(nested_attrs)
        for attr, val in pairs:
            setattr(self, attr, val)

        remove_commas = lambda s: (w.strip() for w in s.split(','))
        prefix_str = self['COMMANDS']['command_prefixes']
        prefixes = tuple(remove_commas(prefix_str))
        self.prefixes = prefixes
        initial_channels_str = self['CREDENTIALS']['initial_channels']
        self.initial_channels = tuple(remove_commas(initial_channels_str))


@dc.dataclass(slots=True)
class RegisteredChannel:
    '''Class for base channel objects instantiated
    from the database and modified as needed.'''
    channel_id: int
    username: str
    display_name: str
    commands: dict = dc.field(default_factory=dict)


@dc.dataclass # (slots=True)
class RegisteredCommand:
    channel_id: int
    name: str
    message: str = dc.field(repr=False)
    author_id: int = dc.field(repr=False)
    # Times in seconds since epoch; use time.gmtime() to convert to UTC
    ctime: int = dc.field(default=round(time.time()), repr=False)
    mtime: int = dc.field(default=round(time.time()), repr=False)
    modified_by: str = dc.field(default=None, repr=False)
    aliases: list[str] = None
    perms: str = 'everyone'
    count: int = 0
    is_hidden: bool = dc.field(default=False)
    is_enabled: bool = dc.field(default=True)
    # override_builtin: bool = dc.field(default=None, repr=False)


class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
    def __init__(self):

        # self.base_command = tuple(remove_commas(config.base_command_name))
        # self.base_aliases = tuple(fuzzy_split(config.base_command_aliases))
        pass

    async def _event_ready(self):
        '''Have the bot do things upon connection to the Twitch server.'''
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
        # msg: str = re.split(r'PRIVMSG\s\#\w+\s:', message.raw_data, 1)[1]
        # Do imdad():
        if msg[:6].lower().startswith(("i'm ", "i am ", "im ")):
            if random.random() < 0.2:
                await message.channel.send(string_commands.imdad(msg))
        # Channel triggers and keywords can eventually be handled here as well.
        await self.handle_commands(message)

    async def _global_before_invoke(self, ctx: Context):
        '''Sets some useful values as Context attributes.'''
        # TwitchIO splits and re-joins message content internally.
        # To preserve message whitespace, regex the raw data from Twitch:
        raw = re.split(r'PRIVMSG\s\#\w+\s:', ctx.message.raw_data, 1)[1]
        ctx.cmd, _, ctx.msg = raw.partition(' ')
        ctx.author_id = int(ctx.author.id)
        channel = await ctx.channel.user()
        ctx.chan_as_user = channel
        # ctx.channel_copy = self._registry.get(channel.id)
        print("--> ", channel.display_name, ctx.cmd, ctx.msg)

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
        return [c.username for c in self._registry.values()]

    def _init_commands(self):
        '''Retrieves command records from the database and
        initializes a `RegisteredCommand` object for each.'''
        fields = ','.join([f.name for f in dc.fields(RegisteredCommand)])
        # cond = "where override_builtin = None"
        cond = ""
        _sql = f"select {fields} from command {cond}"
        records = self._db.execute(_sql)
        for record in records:
            cmd = RegisteredCommand(*record)
            self._registry[cmd.channel_id].commands[cmd.name] = cmd
 
    def get_commands(self, channel_id: int) -> list:
        # return [c for c in self._registry[channel_id].commands]
        return list(self._registry[channel_id].commands.keys())

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
        values = (uid, name, display_name)
        _sql = f"insert into channel({','.join(fields)}) values (?,?,?)"
        try:
            with self._db_conn:
                self._db.execute(_sql, values)
        except sqlite3.Error as exc:
            raise DatabaseError(exc.args[0])

    def _join_channel(self, ctx: Context):
        '''Registers a new channel to the database when invoked within
        the bot's Twitch channel and returns the response to be sent.'''
        resp = ""
        username = ctx.author.name
        display_name = ctx.author.display_name
        error_preface = f"Failed registering channel {username!r}"

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

    def _manage_custom_command(self, ctx: Context, base_name: str = None,
            alias_names: str = None):
        # "addcmd, editcmd, delcmd, disable, enable, alias".split()):
            # config.base_command_aliases.split()):
        '''Parses a `!cmd` string and executes `_add_command()`,
        `_edit_command()` or `_delete_command()` based
        on the implied action.'''

        if base_name is None:
            base_name = self.base_command_name
            # alias_names = fuzzy_split(self.base_command_aliases)
        if alias_names is None:
            alias_names = self.base_aliases

        action_errors = lambda act, cmd: ("Failed to perform requested action",
            f"Failed to {act} command {cmd!r}")[bool(cmd)]
        channel_id = ctx.chan_as_user.id
        if channel_id not in self._registry:
            err = f"Channel with id {channel_id} is not registered."
            raise ChannelNotFoundError(err)

        # alias_names="addcmd editcmd delcmd disable enable alias".split()
        # actions = "add edit delete disable enable alias".split()
        actions = self.cmd_actions
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
        action = ""
        msg = ctx.msg
        body = ctx.msg.split(None, 1)

        if prefixless == base_name and len(body) >= 2:
            (action, msg) = body if len(body) > 1 else ("", body[0])
            syntax = "<cmd syntax>"
            print(action)
            if action not in func_switch:
                err = f"Invalid action: {action!r}. Syntax: {syntax}"
                raise InvalidAction(err)
        elif prefixless in action_switch:
            action = action_switch[prefixless]

        if action in ('delete', 'disable', 'enable', 'alias'):
            return func_switch[action](channel_id, action, msg)

        #parsed = parse_cmd(msg=f"{action} {msg}")
        try:
            parsed = parse_cmd(msg=f"{action} {msg}")
        except (InvalidSyntax, InvalidArgument) as exc:
            err, cmd = exc.args
            error_preface = action_errors(action, cmd)
            exc.args = (f"{error_preface}. {err}",)
            raise exc

        if isinstance(parsed, tuple):
            cmd_dict = vars(parsed[0])
            message = parsed[1]
        elif parsed is None:
            err = """
                Failed to perform requested operation.
                Parser returned NoneType, most likely resulting
                from a --help flag. Those will be implemented soon!"""
            raise NotImplementedError(dedent(err))
        else:
            cmd_dict = vars(parsed)
            message = None

        for arg in ('name', 'new_name', 'aliases'):
            if isinstance(cmd_dict.get(arg), list):
                cmd_dict[arg] = cmd_dict[arg][0]
                #cmd_dict[arg] = cmd_dict[arg] if cmd_dict.get(arg) else None

        name = cmd_dict.get('name')
        new_name = cmd_dict.get('new_name')
        aliases = cmd_dict.get('aliases')
        used_alias = prefixless in action_switch

        cmd_dict['channel_id'] = channel_id
        cmd_dict['message'] = message
        cmd_dict['action'] = action
        cmd_dict['author_id'] = ctx.author_id
        cmd_dict['used_alias'] = used_alias

        if action in ('add', 'edit'):
            # print(f"{cmd_dict=}")
            return func_switch[action](cmd_dict)
        else:
            raise InvalidSyntax(f"Invalid syntax: {action!r}")

    def _add_command(self, cmd_dict: dict):
        '''Adds a custom command to memory and the database.'''
        channel_id = cmd_dict['channel_id']
        name = cmd_dict['name']
        action = cmd_dict.pop('action')
        used_alias = cmd_dict.pop('used_alias')

        actions = self.cmd_actions
        base_name = self.base_command_name
        base_aliases = self.base_aliases
        full_names = (f"!{base_name} {a}" for a in actions)
        aliases = ("!" + a for a in base_aliases)
        alias_switch = dict(zip(actions, zip(full_names, aliases)))

        error_preface = f"Failed to add command {cmd_dict['name']!r}"
        err = ""

        if name in self._registry[channel_id].commands:
            err = f"""
                {error_preface}.
                This command already exists. To change its message or
                properties, use {alias_switch[action][used_alias]!r}}."""
                # {('!cmd edit', '!editcmd')[used_alias]!r}."""
            # Use '!cmd add -h' for details.
            # You can rename it with '!editcmd <oldname> --rename <newname>'.
            # To delete it completely, use '!delcmd'."""
        elif name in self.built_ins:
            err = f"""
                {error_preface}.
                Command name conflicts with a built-in command with the same
                name. Use '--override_builtin' if you want to replace it with
                your custom command. If you change your mind later, simply
                delete the custom command."""
        elif cmd_dict['message'] is None:
            err = f"""
                {error_preface}.
                A message is required when adding a new command.
                Messages must come after any arguments."""
        if err:
            raise RegistrationError(dedent(err))

        attrs = {k: v for k, v in cmd_dict.items() if v is not None}
        cmd = RegisteredCommand(**attrs)
        print("cmd=", dc.asdict(cmd))

        self._registry[channel_id].commands[name] = cmd
        cols, vals = zip(*dc.asdict(cmd).items())
        plchd = ','.join(':' + str(c) for c in cols)
        _sql = f"insert into command ({','.join(cols)}) values ({plchd})"
        try:
            with self._db_conn:
                self._db.execute(_sql, vals)
        except sqlite3.Error as exc:
            err = f"{error_preface}. DatabaseError: {exc.args[0]}"
            raise DatabaseError(err)
        print("Added:", cmd)
        return f"Successfully added command {name}"

    def _edit_command(self, cmd_dict: dict):
        '''Alters a custom command's properties in memory and the database.'''
        channel_id = cmd_dict['channel_id']
        commands = self._registry[channel_id].commands
        name = cmd_dict.get('name')
        new_name = cmd_dict.pop('new_name', None)
        action = cmd_dict.pop('action', None)
        used_alias = cmd_dict.pop('used_alias', None)
        unstored = 'new_name', 'action', 'used_alias'
        error_preface = f"Falied to update command {name!r}"
        err = ""

        if name not in commands and name is not None:
            err = f"""
                {error_preface}. This command does not exist.
                Use '!addcmd' to add it."""
            raise CommandNotFoundError(dedent(err))
        elif new_name in commands:
            err = f"""
                {error_preface}. Naming conflict: The name {new_name!r}
                matches another command with the same name.
                Please find a different new name for {name!r}."""
            raise NameConflict(dedent(err))
        # elif new_name in self.built_ins and not override_builtin:
            # err = f"""
                # {error_preface}. Naming conflict: The name {new_name!r}
                # matches a built-in command with the same name.
                # Use '--override_builtin' if you want to replace it
                # with your custom command. If you change your mind later,
                # simply delete the custom command."""
            # raise NameConflict(dedent(err))

        cmd_dict['name'] = new_name or name
        for key, val in tuple(cmd_dict.items()):
            if val not in unstored and val is not None:
                setattr(self._registry[channel_id].commands[name], key, val)
            else:
                cmd_dict.pop(key)

        # print("cmd_dict:", cmd_dict)

        # keys, vals = zip(*dc.asdict(cmd).items())
        cols = ','.join(cmd_dict.keys())
        params = ','.join(['?'] * len(cmd_dict))
        cond = f"(channel_id, name) = ({channel_id}, {name!r})"
        _sql = f"update command set({cols}) = ({params}) where {cond}"

        try:
            with self._db_conn:
                # self._db.execute(_sql, dc.astuple(cmd))
                self._db.execute(_sql, tuple(cmd_dict.values()))
        except sqlite3.Error as exc:
            err = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(err)
        print("Edited:", self._registry[channel_id].commands[name])
        return f"Successfully updated command {name}"

    def _toggle_command(self, channel_id, action: str, msg: str):
        '''Disable or enable a command by updating
        the database and in-memory dataclass.'''
        names = set(msg.split())
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to {action} {count} command{plur}"
        err = ""

        actions = ('disable', 'enable')
        if action not in actions:
            err = f"""
                Failed to perform requested operation.
                Invalid action: {action!r}"""
            raise InvalidAction(dedent(err))

        attr = 'is_enabled'
        toggle = action == 'enable'
        for name in names:
            if name not in self._registry[channel_id].commands:
                err = f"{error_preface}. Command {name!r} does not exist."
                raise CommandNotFoundError(err)
            self._registry[channel_id].commands[name].is_enabled = toggle

        cond = f"(channel_id, name) = ({channel_id}, ?)"
        _sql = f"update command set is_enabled = ? where {cond}"
        try:
            with self._db_conn:
                self._db.executemany(_sql, zip([toggle] * count, names))
        except sqlite3.Error as exc:
            err = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(err)

        desc = f"{count} command{plur}" if plur else f"command {names.pop()}"
        resp = f"Successfully {action}d {desc}"
        return resp

    def _delete_command(self, channel_id: int, action: str, msg: str):
        '''Delete a command, updating the database and in-memory dataclass.'''
        names = set(msg.split())
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to delete {count} command{plur}"
        err = ""

        for name in names:
            if name in self._registry[channel_id].commands:
                del self._registry[channel_id].commands[name]
            elif name in self.built_ins:
                err = f"""
                    {error_preface}. Command {name!r} is a built-in command.
                    It cannot be deleted, but you may disable
                    it with '!disable {name}'."""
                raise NameConflict(dedent(err))
            else:
                err = f"{error_preface}. Command {name!r} does not exist."
                raise CommandNotFoundError(err)

        cond = f"(channel_id, name) = ({channel_id}, ?)"
        _sql = f"delete from command where {cond}"
        try:
            with self._db_conn:
                self._db.executemany(_sql, zip(names))
        except sqlite3.Error as exc:
            err = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(err)
        desc = f"{count} command{plur}" if plur else f"command {names.pop()}"
        resp = f"Successfully deleted {desc}"
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
