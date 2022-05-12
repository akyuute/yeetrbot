# from built_in_commands import core_commands, text_commands, math_commands
# import built_in_commands
# from commands import CoreCommands
# from optional_commands import OptionalCommands
import commands
from parsing import (cmd_add_parser, cmd_edit_parser,
    CMD_ARGUMENT_FLAGS)
from errors import *
from twitchio import Client, Message
from base_classes import Config, RegisteredChannel, Context, CustomCommand, BuiltInCommand

import re
import sys
import time
import random
import sqlite3
import inspect
import itertools
import dataclasses as dc
from textwrap import dedent


class Yeetrbot(Client):
    '''Contains methods for database exchanges and basic bot functionality.'''

    def __init__(self, config: Config | dict):
        self._db_file = config['DATABASE'].get('db_file', 'db/bot.db')
        self._channels = {}
        self._built_in_commands = {}
        self._built_in_aliases = {}
        self.syntaxes = commands.CoreCommands.SYNTAXES.copy()
        self.display_name = config['CREDENTIALS']['bot_nick']

        cmd_conf = config['COMMANDS']

        #self._prefixes = cmd_conf.get('command_prefixes', "!").split()
        #print("ChatBot prefixes:", self._prefixes)

        self._base_command_name = cmd_conf['base_command_name']
        self._default_perms = cmd_conf.get('default_perms', "everyone")
        self._default_count = int(cmd_conf.get('default_count', 0))
        self._default_cooldowns = cmd_conf.get("default_cooldowns")
        self._require_message = config.require_message
        self._override_builtins = config.override_builtins
        self._case_sensitive_commands = config.case_sensitive

        aliases = (a for a in cmd_conf.items() if '_command_alias' in a[0])
        alias_dict = {k.removesuffix('_command_alias'): v for k, v in aliases}
        self._base_command_aliases = alias_dict

        initial_channels = config['CREDENTIALS']['initial_channels'].split()
        self._initial_channels = set(initial_channels + self.channels)

        super().__init__(
            token=config['CREDENTIALS']['access_token'],
            client_secret=config['CREDENTIALS']['client_id'],
            initial_channels=self._initial_channels
            )

        self._init_database(self._db_file)
        self._init_channels()
        self._init_builtins()

    @property
    def channels(self) -> list:
        return [channel for channel in self._channels.values()]
    
    @property
    def built_in_commands(self) -> dict:
        return self._built_in_commands

    #@property
    #def prefixes(self) -> tuple:
        #return self._prefixes

    def _init_database(self, db_file: str):
        '''Connects to the sqlite3 database and creates it if necessary.'''
        self._db_conn = sqlite3.connect(db_file)
        self._db = self._db_conn.cursor()
        # with self._db_conn:
        with open('db/schema.sql', 'r') as f:
            self._db.executescript(f.read())

    def _init_channels(self):
        '''Retrieves channel records from the database and
        initializes a `RegisteredChannel` object for each.'''
        records = self._db.execute("select * from channel")
        for record in records:
            channel_id = record[0]
            self._channels[channel_id] = RegisteredChannel(*record, bot=self)

    def _init_builtins(self, cls = BuiltInCommand):
        core_cmds = (
            cls(name=f.__name__, func=f) for f in vars(commands.CoreCommands).values()
            if callable(f))
        opt_cmds = (c for _, c in inspect.getmembers(commands) if
            isinstance(c, cls))
        cust_cmds = (c for _, c in inspect.getmembers(self) if
            isinstance(c, cls))

        cmds = itertools.chain(core_cmds, opt_cmds, cust_cmds)

        # print("Length of chain of cmds:", len(list(cmds)))
        for cmd in cmds:
            # print("Hellp?")
            self.load_builtin(cmd)
            print(cmd.name)

        print(self._built_in_aliases)

        _sql = "select * from channel_built_in"
        records = self._db.execute(_sql)
        for record in records:
            channel_id = record[0]
            command = dict(record)
            print("Built-in:", command)

    def load_builtin(self, command) -> None:
        '''Load a built-in command for use globally.'''
        cls = BuiltInCommand
        error_preface = f"Failed to load built-in command {command.name!r}: "

        if not isinstance(command, cls):
            raise TypeError(error_preface +
                f"Built-in commannds must be of type {cls}.")
        elif command.name in self._built_in_commands:
            raise NameConflict(error_preface +
                f"A built-in command with this name is already loaded.")
        elif not inspect.iscoroutinefunction(command._callback):
            raise RegistrationError(error_preface +
                f"Command callbacks must be coroutines.")

        command._instance = self
        self._built_in_aliases[command.name] = command

        _sql = "insert into built_in_command(name, global_aliases) values (?,?)"
        values = (command.name, ','.join(command._aliases))
        self._db.execute(_sql, values)
        self._db_conn.commit()

        if not command._aliases:
            return
        for alias in command._aliases:
            if alias in self._built_in_aliases:
                # self._built_in_commands.pop(command.name)
                raise NameConflict(error_preface +
                    f"A built-in command with the same name or alias is "
                    f"already loaded.")
            self._built_in_aliases[alias] = command


    def _init_commands(self):
        '''Retrieves command records from the database and
        initializes a `CustomCommand` object for each.'''
        fields = ','.join([f.name for f in dc.fields(CustomCommand)])
        #fields = ','.join(CustomCommand.__slots__)
        # cond = "where override_builtin = None"
        cond = ""
        _sql = f"select {fields} from command {cond}"
        records = self._db.execute(_sql)
        for record in records:
            cmd = CustomCommand(*record)
            self._channels[cmd.channel_id].commands[cmd.name] = cmd

 
    def register_channel(self, uid: int, name: str):
        '''Registers a channel to the database if new, otherwise raises
        `RegistrationError`. This must only be called by a command sent
        in the bot's channel.'''
        if uid in self._channels:
            error = f"Channel {name!r} is already registered."
            raise RegistrationError(error)
        channel = RegisteredChannel(uid, name)
        self._channels[uid] = channel
        fields = ('id', 'name')
        values = (uid, name)
        # opt = ""
        opt = "or replace"
        _sql = f"insert {opt} into channel({','.join(fields)}) values (?,?)"
        try:
            self._db.execute(_sql, values)
        except sqlite3.Error as exc:
            self._channels.pop(uid)
            raise DatabaseError(exc.args[0])

    def refresh_user_data(self, user_id: int, name: str):
        '''Updates a channel's name if the username changes.'''
        fields = ('id', 'name')
        values = (user_id, name)
        _sql = f"update set channel({','.join(fields)}) = (?,?)"
        try:
            self._db.execute(_sql, values)
        except sqlite3.Error as exc:
            raise DatabaseError(exc.args[0])

    def _manage_custom_command(self, ctx: Context):
        '''Parses a `!cmd` string and executes `_add_command()`,
        `_edit_command()` or `_delete_command()` based on implied action.'''

        channel_id = ctx.channel_id
        if channel_id not in self._channels:
            error = f"Channel with id {channel_id} is not registered."
            raise ChannelNotFoundError(error)

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
        #prefixless = ctx.cmd.removeprefix(ctx.prefix)
        #prefix_base = ctx.prefix + self._base_command_name
        cmd_name = ctx.command.name
        prefix_base = ctx._base_command_name
        base_opts = "<command> [options ...]"
        base_usage = f"{prefix_base} {{{' | '.join(actions)}}} {base_opts}"

        action = ""
        msg = ctx.msg
        body = msg.split(None, 1) if msg else ""

        if cmd_name == self._base_command_name and body:
            (action, msg) = body if len(body) > 1 else (body[0], "")
        else:  # If cmd_name is in alias_switch.values()...
            action = {v: k for k, v in alias_switch.items()}.get(cmd_name)

        if len(msg.split()) == 1:
            name, msg = (msg, "")
        else:
            name, msg = msg.split(None, 1) or (msg, "")

        if action in ('delete', 'disable', 'enable', 'alias'):
            names = set(ctx.msg.split())
            if not names:
                error = f"""
                Invalid syntax. Please specify at least
                one valid command name to {action}."""
                raise InvalidSyntax(dedent(error))
            return func_switch[action](channel_id, action, names)

        if action not in actions:
            error = f"""
                Invalid action: {action!r}.
                {ctx.cmd} usage: {base_usage!r}"""
            raise InvalidAction(dedent(error))

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
            '\n .').partition('[')[2].replace(
                "ALIASES", "<aliases>").replace("COUNT", "<count>")
        usage = dedent(f"""
            {base_or_alias} syntax: '{base_or_alias} <name>
            [{add_or_edit_usage} {message_repr}'""")

        if name in CMD_ARGUMENT_FLAGS or not msg:
            if name in ('--help', '-h'):
                args = msg.split()
                print("name:", name)
                print("Got --help in", repr([name] + args))
                # args = (k for k, v in cmd_dict.items() if v is not None)
                # print(list(args))
                resp = f"""
                    {base_and_alias[action][used_alias]} syntax:
                    {self._get_syntax(action, args)}"""
                return dedent(resp)
                return usage
            existing_or_new = ("an existing", "a new")[action == 'add']
            error =  f"""
                Invalid syntax. The first argument of
                {base_or_alias} must be {existing_or_new} command name."""
            raise InvalidSyntax(dedent(error))
        # elif not msg:
            # return usage

        error_preface = f"Failed to {action} command {name!r}"

        update_err_dict = {
            'add': [{
                'test': name in self._channels[channel_id].commands,
                'exc': NameConflict(dedent(f"""
                    {error_preface}.
                    This command already exists. To change its message or
                    properties, use 
                    {base_and_alias['edit'][used_alias]!r}."""))
                }, {

                'test': name in self.built_in_commands,
                'exc': NameConflict(dedent(f"""
                    {error_preface}.
                    Command name conflicts with a built-in command with the
                    same name. Use '--override_builtin' if you want to replace
                    it with your custom command. If you change your mind
                    later, simply delete the custom command."""))
                },
            ],

            'edit': [{
                'test': name not in self._channels[channel_id].commands,
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

        if cmd_dict.get('help') is True:
            args = msg.split()
            print("Got --help in", repr(args))
            # args = (k for k, v in cmd_dict.items() if v is not None)
            # print(list(args))
            resp = f"""
                {base_and_alias[action][used_alias]} syntax:
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
        print("cmd_dict: ", cmd_dict)

        for error in update_err_dict[action]:
            if error['test']:
                raise error['exc']

        if action in ('add', 'edit'):
            return func_switch[action](cmd_dict)
        else:
            raise InvalidSyntax(f"Invalid syntax: {action!r}")

    def _add_command(self, cmd_dict: dict):
        '''Adds a custom command to memory and the database.'''
        cmd_dict.setdefault('author_id', cmd_dict['modified_by'])
        cmd_dict.setdefault('perms', self._default_perms)
        cmd_dict.setdefault('count', self._default_count)
        cmd_dict.setdefault('cooldowns', self._default_cooldowns)
        cmd_dict.setdefault('case_sensitive', self._case_sensitive_commands)
        channel_id = cmd_dict['channel_id']
        name = cmd_dict['name']
        cmd_dict.pop('action')
        base_or_alias = cmd_dict.pop('base_or_alias')

        error_preface = f"Failed to add command {name!r}"
        error = ""

        if cmd_dict['message'] is None and self._require_message:
            error = f"""
                {error_preface}.
                A message is required when adding a new command.
                Messages must come after any arguments."""
            raise RegistrationError(dedent(error))

        attrs = {k: v for k, v in cmd_dict.items() if v is not None}
        cmd = CustomCommand(**attrs)
        # print("cmd = ", dc.asdict(cmd))

        self._channels[channel_id].commands[name] = cmd
        cols, vals = zip(*dc.asdict(cmd).items())
        plchd = ','.join(':' + str(c) for c in cols)
        _sql = f"insert into command ({','.join(cols)}) values ({plchd})"
        try:
            with self._db_conn:
                self._db.execute(_sql, vals)
        except sqlite3.Error as exc:
            error = f"{error_preface}. DatabaseError: {exc.args[0]}"
            raise DatabaseError(error)
        print("Added:", cmd)
        return f"Successfully added command {name}."

    def _edit_command(self, cmd_dict: dict):
        '''Alters a custom command's properties in memory and the database.'''
        channel_id = cmd_dict['channel_id']
        commands = self._channels[channel_id].commands
        name = cmd_dict.pop('name')
        new_name = cmd_dict.pop('new_name')
        new_name = new_name[0] if isinstance(new_name, list) else None
        modified_by = cmd_dict
        base_or_alias = cmd_dict.pop('base_or_alias')
        action = cmd_dict.pop('action')

        error_preface = f"Falied to update command {name!r}"
        error = ""

        if new_name in commands:
            error = f"""
                {error_preface}. Naming conflict: The name {new_name!r}
                matches another command with the same name.
                Please find a different new name for {name!r}."""
            raise NameConflict(dedent(error))
        elif new_name in self.built_in_commands : # and not override_builtin:
            error = f"""
                {error_preface}. Naming conflict: The name {new_name!r}
                matches a built-in command with the same name.
                Use '--override_builtin' if you want to replace it
                with your custom command. If you change your mind later,
                simply delete the custom command."""
            raise NameConflict(dedent(error))

        # Dict changes size, hence conversion to tuple:
        for key, val in tuple(cmd_dict.items()):
            if val is not None:
                setattr(self._channels[channel_id].commands[name], key, val)
            else:
                cmd_dict.pop(key)
        if new_name:
            cmd_dict['name'] = new_name
            new_cmd = self._channels[channel_id].commands.pop(name)
            self._channels[channel_id].commands[new_name] = new_cmd

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
            error = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(error)
        print("Edited:", self._channels[channel_id].commands.get(name) or new_cmd)
        resp = f"Successfully updated command {name}"
        resp += f" and renamed it {new_name!r}." if new_name else "."
        return resp

    def _toggle_command(self, channel_id, action: str, names: set):
        '''Disable or enable a command by updating
        the database and in-memory dataclass.'''
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to {action} {count} command{plur}"
        error = ""

        actions = ('disable', 'enable')
        if action not in actions:
            error = f"""
                Failed to perform requested operation.
                Invalid action: {action!r}"""
            raise InvalidAction(dedent(error))

        attr = 'is_enabled'
        toggle = action == 'enable'
        for name in names:
            if name not in self._channels[channel_id].commands:
                error = f"{error_preface}. Command {name!r} does not exist."
                raise CommandNotFoundError(error)
            self._channels[channel_id].commands[name].is_enabled = toggle

        cond = f"(channel_id, name) = ({channel_id}, ?)"
        _sql = f"update command set is_enabled = ? where {cond}"
        try:
            with self._db_conn:
                self._db.executemany(_sql, zip([toggle] * count, names))
        except sqlite3.Error as exc:
            error = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(error)

        desc = f"{count} command{plur}" if plur else f"command {names.pop()}"
        resp = f"Successfully {action}d {desc}."
        return resp

    def _delete_command(self, channel_id: int, action: str, names):
        '''Delete a command, updating the database and in-memory dataclass.'''
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to delete {count} command{plur}"
        error = ""

        for name in names:
            if name in self._channels[channel_id].commands:
                del self._channels[channel_id].commands[name]
            elif name in self.built_in_commands:
                error = f"""
                    {error_preface}. Command {name!r} is a built-in command.
                    It cannot be deleted, but you may disable
                    it with '!disable {name}'."""
                raise NameConflict(dedent(error))
            else:
                error = f"{error_preface}. Command {name!r} does not exist."
                raise CommandNotFoundError(error)

        cond = f"(channel_id, name) = ({channel_id}, ?)"
        _sql = f"delete from command where {cond}"
        try:
            with self._db_conn:
                self._db.executemany(_sql, zip(names))
        except sqlite3.Error as exc:
            error = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(error)
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



#    def _get_prefix(self, message: Message) -> str|None:
#        prefixes = self._prefixes
#        if not isinstance(prefixes, str):
#            for prefix in prefixes:
#                if message.content.startswith(prefix):
#                    return prefix
#        elif message.content.startswith(prefixes):
#            return prefixes
#        else:
#            return None

#    def _get_command(self, ctx: Context) -> str|None:
#        '''Gets a potential command name from the first word of a message if
#        the message begins with a valid prefix, otherwise returns `None`.
#        Note that if `command_prefixes` are left blank in the config, every
#        message will be treated as a command.'''
#        if ctx.prefix is not None:
#            msg = ctx.message.content
#            return msg.partition(" ")[0] # .lstrip(ctx.prefix)

    def get_custom_commands(self, channel_id: int) -> list:
        return list(self._channels[channel_id].commands)
        # return (c for c in self._channels[channel_id].commands)

    def _get_syntax(self, command: str, args="", syntaxes: dict = None):
        '''Returns the syntax/usage statement of a built-in command. Raises
        `CommandNotFoundError` if the command does not exist.'''
        if syntaxes is None:
            syntax = self.syntaxes[command]
        else:
            syntax = syntaxes[command]
        # if command not in self.built_in_commands:
            # error = f"Built-in command {command!r} does not exist."
            # raise CommandNotFoundError(error)
        args = args.split() if args and isinstance(args, str) else [""]
        if set(syntax).isdisjoint(set(args)):
            raise ValueError("No arguments in list")
        return ' '.join(syntax.get(m, "") for m in set(args))

    async def get_command(self, context: Context) -> CustomCommand|BuiltInCommand:
        channel = self._channels[context.channel_id]
        command_or_alias = context.message.content.partition(" ")[0]
        if self._case_sensitive_commands:
            command_name = command_or_alias 
        else:
            command_name = command_or_alias.lower()

        if command_name in channel._command_aliases:
            #command = channel._commands[channel._command_aliases[command_name]]
            command = chann
        elif command_name in channel._built_in_aliases:
            command = channel._built_ins.get(command_name)
        #elif command_name in self._built_in_aliases:

        return channel._command_aliases.get(command_, None)

    async def get_context(self, message: Message) -> Context:
        '''Returns a `Context` object made from a `Message` returned by
        `event_message` after setting its attributes.'''
        context = Context(bot=self, message=message)
        context.prefix = "!"  # Remove after fixing cmd management
        command_name = context.message.content.partition(" ")[0]
        command = await context.channel.resolve_command(command_name)
        if command is None:
            # print("No command found in channel commands. Searching bot built-ins...")
            for alias, cmd in self._built_in_aliases.items():
                if context.message.content.startswith(alias):
                    context.command = cmd
                    context.invoked_with = alias
                    print("Found command:", cmd.name)
        return context

    async def handle_commands(self, context: Context):
        # if context._command_name in self._built_in_aliases:
            # return await self.built_in_commands[context.command](context)
        if context.command is not None : #  or context.is_valid is not False:
            return await context.command(context)
        await self.handle_keywords(context)


    async def handle_keywords(self, context: Context):
        #print(f"Got keyword in message {context.message.content!r}")
        pass


    async def event_ready(self):
        '''Have the bot do things upon connection to the Twitch server.'''
        print(f"{self.display_name} is online!")
        print("Connected channels:", self.connected_channels)
        # Post a message in each registered channel's chat upon connection:
        # for channel in self.connected_channels:
        # notify = f"{self.display_name} is online!"
        #     await self.get_channel(channel).send(msg)
        #     pass

    async def event_message(self, message: Message):
        if message.echo:
            return
        #print(message.raw_data)
        # print(f"{context.channel.name} -> {context.message.content}")
        print(f"{context.author.name} -> {context.message.content}")
        context = await self.get_context(message)
        # print(context.channel._command_aliases)
        await self.handle_commands(context)


if __name__ == '__main__':
    pass
    # bot = Yeetrbot(config=Config('bot.conf'))

