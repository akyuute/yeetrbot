import re
import sys
import time
import random
import sqlite3
import dataclasses as dc
from typing import Callable
from textwrap import dedent
from argparse import ArgumentParser
from configparser import ConfigParser
from twitchio.ext.commands import Context

from my_commands import string_commands
import my_commands.built_ins as built_in_commands
from parsing import (cmd_add_parser, cmd_edit_parser,
    cmd_add_or_edit, valid_parser_flags)
from errors import (
    ChannelNotFoundError,
    CommandNotFoundError,
    RegistrationError,
    NameConflict,
    InvalidAction,
    InvalidSyntax,
    ParsingError,
    DatabaseError,
    )


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
    message: str
    author_id: int
    modified_by: int
    aliases: list[str] = None
    perms: str = 'everyone'
    count: int = 0
    # Times in seconds since epoch; use time.gmtime() to convert to UTC
    ctime: int = round(time.time())
    mtime: int = round(time.time())
    is_hidden: bool = False
    is_enabled: bool = True
    # override_builtin: bool = None


class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
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
 
    # @property
    # def channels(self):
        # '''A list of registered channel names.'''
        # return [c.username for c in self._registry.values()]

    @property
    def registered_channels(self) -> list:
        registered_channels = [c.username for uid, c in self._registry.items()]
        return registered_channels

    def get_commands(self, channel_id: int) -> list:
        return list(self._registry[channel_id].commands)

    def _get_syntax(self, command: str, args="", syntaxes: dict = None):
        '''Returns the syntax/usage statement of a built-in command. Raises
        `CommandNotFoundError` if the command does not exist.'''
        if syntaxes is None:
            syntax = self.syntaxes[command]
        # if command not in self.built_ins:
            # err = f"Built-in command {command!r} does not exist."
            # raise CommandNotFoundError(err)
        args = args.split() if args and isinstance(args, str) else [""]
        if set(syntax).isdisjoint(set(args)):
            raise ValueError("No arguments in list")
        return ' '.join(syntax.get(m, "") for m in set(args))

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

    def _manage_custom_command(self, ctx: Context):
        '''Parses a `!cmd` string and executes `_add_command()`,
        `_edit_command()` or `_delete_command()` based on implied action.'''

        channel_id = ctx.chan_as_user.id
        if channel_id not in self._registry:
            err = f"Channel with id {channel_id} is not registered."
            raise ChannelNotFoundError(err)

        alias_switch = self._base_command_aliases
        actions = alias_switch.keys()
        func_switch = {
            'add': self._add_command,
            'edit': self._edit_command,
            'delete': self._delete_command,
            'disable': self._toggle_command,
            'enable': self._toggle_command,
            'alias': self._edit_command
        }
        prefixless = ctx.cmd.removeprefix(ctx.prefix)
        prefix_base = ctx.prefix + self._base_command_name
        base_opts = "<command> [options ...]"
        base_usage = f"{prefix_base} {{{' | '.join(actions)}}} {base_opts}"

        action = ""
        msg = ctx.msg
        body = msg.split(None, 1) if msg else ""

        if prefixless == self._base_command_name and body:
            (action, msg) = body if len(body) > 1 else (body[0], "")
        else:  # If prefixless is in alias_switch.values()...
            action = {v: k for k, v in alias_switch.items()}.get(prefixless)

        if len(msg.split()) == 1:
            name, msg = (msg, "")
        else:
            name, msg = msg.split(None, 1) or (msg, "")

        if action in ('delete', 'disable', 'enable', 'alias'):
            names = set(ctx.msg.split())
            if not names:
                err = f"""
                Invalid syntax. Please specify at least
                one valid command name to {action}."""
                raise InvalidSyntax(dedent(err))
            return func_switch[action](channel_id, action, names)

        if action not in actions:
            err = f"""
                Invalid action: {action!r}.
                {ctx.cmd} usage: {base_usage!r}"""
            raise InvalidAction(dedent(err))

        get_base_and_alias = lambda a: (
            f"{prefix_base} {a}",
            ctx.prefix + alias_switch[a])
        base_and_alias = {a: get_base_and_alias(a) for a in ('add', 'edit')}
        used_alias = prefixless in alias_switch.values()
        base_or_alias = (
            f"{prefix_base} {action}",
            ctx.prefix + alias_switch.get(action, action))[used_alias]

        msg_repr_fmts = ("[message]", "<message>")
        message_repr = msg_repr_fmts[self._require_message and action == 'add']
        parsers = {'add': cmd_add_parser, 'edit': cmd_edit_parser}
        add_or_edit_usage = parsers[action].format_usage().strip(
            '\n .').partition('[')[2].replace("ALIASES", "<aliases>")
        usage = dedent(f"""
            {base_or_alias} syntax: '{base_or_alias} <name>
            [{add_or_edit_usage} {message_repr}'""")

        if name in valid_parser_flags:
            new_or_existing = ("an existing", "a new")[action == 'add']
            err =  f"""
                Invalid syntax. The first argument of
                {base_or_alias} must be {new_or_existing} command name."""
            raise InvalidSyntax(dedent(err))
        elif not msg:
            return usage

        error_preface = f"Failed to {action} command {name!r}"

        update_err_dict = {
            'add': [{
                'test': name in self._registry[channel_id].commands,
                'exc': NameConflict(dedent(f"""
                    {error_preface}.
                    This command already exists. To change its message or
                    properties, use 
                    {base_and_alias['edit'][used_alias]!r}."""))
                }, {

                'test': name in self.built_ins,
                'exc': NameConflict(dedent(f"""
                    {error_preface}.
                    Command name conflicts with a built-in command with the
                    same name. Use '--override_builtin' if you want to replace
                    it with your custom command. If you change your mind
                    later, simply delete the custom command."""))
                },
            ],

            'edit': [{
                'test': name not in self._registry[channel_id].commands,
                'exc': CommandNotFoundError(dedent(f"""
                    {error_preface}.
                    This command does not exist.
                    To add it, use {base_and_alias['add'][used_alias]!r}."""))
                },
            ]
        }

        args = msg.split(' ')
        try:
            parsed = parsers[action].parse_args(args)
        except ParsingError as exc:
            raise ParsingError(f"{error_preface}. {exc.args[0].capitalize()}")

        cmd_dict = vars(parsed)
        print(cmd_dict)

        if cmd_dict.get('help') is True:
            args = msg.split()
            print(repr(args))
            # args = (k for k, v in cmd_dict.items() if v is not None)
            # print(list(args))
            resp = f"""
                {base_or_alias[action][used_alias]} syntax:
                {self._get_syntax(action, args)}"""
            return dedent(resp)
            return usage


        cmd_dict.update(
            channel_id=channel_id,
            name=name,
            message= ' '.join(cmd_dict.get('message')) or None,
            action=action,
            modified_by=ctx.author_id,
            mtime=round(time.time()),
            base_or_alias=base_or_alias
        )

        for err in update_err_dict[action]:
            if err['test']:
                raise err['exc']

        if action in ('add', 'edit'):
            return func_switch[action](cmd_dict)
        else:
            raise InvalidSyntax(f"Invalid syntax: {action!r}")

    def _add_command(self, cmd_dict: dict):
        '''Adds a custom command to memory and the database.'''
        cmd_dict.setdefault('author_id', cmd_dict['modified_by'])
        cmd_dict.setdefault('perms', self._default_perms)
        cmd_dict.setdefault('count', self._default_count)
        channel_id = cmd_dict['channel_id']
        name = cmd_dict['name']
        cmd_dict.pop('action')
        base_or_alias = cmd_dict.pop('base_or_alias')

        error_preface = f"Failed to add command {name!r}"
        err = ""

        if cmd_dict['message'] is None and self._require_message:
            err = f"""
                {error_preface}.
                A message is required when adding a new command.
                Messages must come after any arguments."""
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
        return f"Successfully added command {name}."

    def _edit_command(self, cmd_dict: dict):
        '''Alters a custom command's properties in memory and the database.'''
        channel_id = cmd_dict['channel_id']
        commands = self._registry[channel_id].commands
        name = cmd_dict.pop('name')
        new_name = cmd_dict.pop('new_name', None)
        modified_by = cmd_dict
        base_or_alias = cmd_dict.pop('base_or_alias')
        action = cmd_dict.pop('action')

        error_preface = f"Falied to update command {name!r}"
        err = ""

        if new_name in commands:
            err = f"""
                {error_preface}. Naming conflict: The name {new_name!r}
                matches another command with the same name.
                Please find a different new name for {name!r}."""
            raise NameConflict(dedent(err))
        elif new_name in self.built_ins : # and not override_builtin:
            err = f"""
                {error_preface}. Naming conflict: The name {new_name!r}
                matches a built-in command with the same name.
                Use '--override_builtin' if you want to replace it
                with your custom command. If you change your mind later,
                simply delete the custom command."""
            raise NameConflict(dedent(err))

        # Dict changes size, hence conversion to tuple:
        for key, val in tuple(cmd_dict.items()):
            if val is not None:
                setattr(self._registry[channel_id].commands[name], key, val)
            else:
                cmd_dict.pop(key)
        if new_name:
            cmd_dict['name'] = new_name
            new_cmd = self._registry[channel_id].commands.pop(name)
            self._registry[channel_id].commands[new_name] = new_cmd

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
        print("Edited:", self._registry[channel_id].commands.get(name) or new_cmd)
        resp = f"Successfully updated command {name}"
        resp += f" and renamed it {new_name!r}." if new_name else "."
        return resp

    def _toggle_command(self, channel_id, action: str, names: set):
        '''Disable or enable a command by updating
        the database and in-memory dataclass.'''
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
        resp = f"Successfully {action}d {desc}."
        return resp

    def _delete_command(self, channel_id: int, action: str, names):
        '''Delete a command, updating the database and in-memory dataclass.'''
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
