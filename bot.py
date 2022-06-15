# from built_in_commands import core_commands, text_commands, math_commands
# import built_in_commands
# from commands import CoreCommands
# from optional_commands import OptionalCommands
import commands
import parse_commands
from parsing import (cmd_add_parser, cmd_edit_parser,
    CMD_ARGUMENT_FLAGS)
from errors import *
from twitchio import Client, Message
from base_classes import Config, RegisteredChannel, Context, CustomCommand, BuiltInCommand
# from parse_commands import ManageCmdParser

import re
import sys
import time
import random
import asyncio
import sqlite3
import inspect
import itertools
import dataclasses as dc
from textwrap import dedent


class Yeetrbot(Client):
    '''Contains methods for database exchanges and basic bot functionality.'''

    def __init__(self, config: str):

        self.cfg = Config(config)
        core_cmd_cfgs = self.cfg.commands['core_built_ins']

        for c in core_cmd_cfgs:
            if core_cmd_cfgs[c].get('aliases'):
                core_cmd_cfgs[c]['aliases'].remove('')

        self.cmd_manager = parse_commands.ManageCmdParser(self)
        core_cmd_cfgs[
                'cmd_manage_commands'][
                    'fn_switch'] = {
                        'add': self.cmd_manager.add_command,
                        'edit': self.cmd_manager.edit_command,
                        'delete': self.cmd_manager.delete_command,
                        'disable': self.cmd_manager.toggle_command,
                        'enable': self.cmd_manager.toggle_command,
                        #'alias': self.cmd_manager.edit_command
                    }

        # self._db_file = config['DATABASE'].get('db_file', 'db/bot.db')
        self._channels = {}
        # self.syntaxes = commands.CoreCommands.SYNTAXES.copy()
        # self.display_name = config['CREDENTIALS']['bot_nick']
        self.display_name = self.cfg.bot.get('display_name')

        # self._base_command_name = cmd_conf['base_command_name']
        # self._default_perms = cmd_conf.get('default_perms', "everyone")
        # self._default_count = int(cmd_conf.get('default_count', 0))
        # self._default_cooldowns = cmd_conf.get("default_cooldowns")
        # self._require_message = config.require_message
        # self._override_builtins = config.override_builtins
        # self._case_sensitive_commands = config.case_sensitive

        initial_channels = self.cfg.bot.get('initial_channels')
        self._initial_channels = set(initial_channels + self.channels)
        creds = self.cfg.bot['credentials']

        super().__init__(
            token=creds['token'],
            client_secret=creds.get('client_secret') or creds.get('client_id'),
            #client_id=creds['client_id'],
            initial_channels=self._initial_channels
            )

        # print(self.user_id)
        self._built_in_commands = {}
        self._built_in_command_aliases = {}
        self._init_database(self.cfg.database['file'])
        self._init_builtins()
        self._init_channels()

        # self._built_in_lookup = {a.lower(): c for a, c in
            # self._built_in_command_aliases.items()}

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
        self._db_conn.row_factory = sqlite3.Row
        self._db = self._db_conn.cursor()
        with open('db/schema.sql', 'r') as f:
            self._db.executescript(f.read())

    def _init_channels(self):
        '''Retrieves channel records from the database and
        initializes a `RegisteredChannel` object for each.'''
        # Initialize the bot's channel.
        #await self.register_channel(self.user_id, self.display_name)

        records = self._db.execute("select * from channel")
        for record in records:
            # print(f"{dict(record) = }")
            channel = RegisteredChannel(*record, bot=self)
            # channel._alias_lookup.update(self._built_in_lookup)
            # channel._alias_lookup = itertools.chain(
                # channel.custom_command_aliases.items(),
                # self._built_in_command_aliases.items()
            # )
            self._channels[channel.id] = channel

    def _init_builtins(self, cls = BuiltInCommand):
        # Init the core built-ins:
        BASE_CMD_FUNC = 'cmd_manage_commands'
        ACTION_ALIASES = 'action_aliases'
        core_cfg = self.cfg.commands['core_built_ins']
        core_cmds = []

        for f in vars(commands.CoreCommands).values():
            if not callable(f):
                continue

            buin = core_cfg.get(f.__name__, None)
            if buin is None:
                continue

            name = buin.get('name') or f.__name__
            aliases = buin.get('aliases')

            if f.__name__ == BASE_CMD_FUNC:
                action_aliases = core_cfg[f.__name__].get(ACTION_ALIASES)
                aliases += action_aliases.values()

            perms = buin.get('perms') or self.cfg.commands.get('default_perms')
            count = buin.get('count') or self.cfg.commands.get('default_count')

            cmd = cls(
                name=name,
                callback=f,
                # global_aliases=aliases,
                aliases=aliases,
                perms=perms,
                count=count
            )

            core_cmds.append(cmd)
                # cls(**buin)


        # core_cmds = (
            # cls(
                # name=core_cfg.get(f.__name__).get('name') or f.__name__,
                # aliases=
                # callback=f
            # ) for f in
            # vars(commands.CoreCommands).values() if callable(f))

        opt_cmds = (c for _, c in
            inspect.getmembers(commands) if isinstance(c, cls))
        cust_cmds = (c for _, c in
            inspect.getmembers(self) if isinstance(c, cls))

        cmds = itertools.chain(core_cmds, opt_cmds, cust_cmds)

        # print("Length of chain of cmds:", len(list(cmds)))
        for cmd in cmds:
            # print(cmd)
            self.load_builtin(cmd)
            print("Loaded built-in:", cmd.name)

        # print(self._built_in_command_aliases)

        # self._db.row_factory = sqlite3.Row
        _sql = """
        select * from built_in_command l inner join
        channel_built_in_data r on l.id = r.command_id"""
        records = self._db.execute(_sql)
        for record in records:
            data = dict(**record)
            data.pop('id')
            # data_dict = {k: v for k, v in dict(record).items()
                # if k != 'id' and v is not None}
            try:
                fn = self._built_in_command_aliases.get(data['name']).callback
            except KeyError as e:
                print(f"Built-in command {data['name']!r} does not exist.")
            except AttributeError as e:
                print(f"Built-in command {data['name']!r} has no callback.")
            channel_id = data['channel_id']
            command = BuiltInCommand(**data, bot=self, callback=fn)
            self._channels[channel_id] = command
            # print("Built-in:", command)

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
        elif not inspect.iscoroutinefunction(command.callback):
            raise RegistrationError(error_preface +
                f"Command callbacks must be coroutines.")

        # print(f"{command = }")
        # print(f"{self._built_in_command_aliases = }")

        # command.bot = self
        self._built_in_command_aliases[command.name] = command

        # _sql = """
            # INSERT OR UPDATE INTO
        _sql = """INSERT OR IGNORE INTO
            built_in_command(name, global_aliases)
            VALUES (?,?)"""
        values = (command.name, ','.join(command.global_aliases or ""))
        self._db.execute(_sql, values)
        self._db_conn.commit()

        if not command.aliases:
            return
        for alias in command.aliases:
            if alias in self._built_in_command_aliases:
                # self._built_in_commands.pop(command.name)
                raise NameConflict(error_preface +
                    f"A built-in command with the same name or alias is "
                    f"already loaded.")
            self._built_in_command_aliases[alias] = command

    
        _sql = """
            select * from built_in_command l
            left join channel_built_in_data r
            on l.id = r.command_id"""
        records = self._db.execute(_sql)
        for row in records:
            pass
            # print(dict(**row))
        # print(dict(**row for row in records))


    def load_channel_builtin(self, channel_id: int, command):
        cfg = self.cfg.commands
        attrs = {
             'channel_id': channel_id,
             'perms': cfg.default_perms,
             'count': cfg.default_count,
        }

        for attr, default in attrs.items():
            if getattr(command, attr) is None:
                setattr(command, attr, default)

        # if command.count is None:
            # command.count = cfg['default_count']
            # command.count = cfg['default_count']
        self._channels[channel_id]._command_aliases[command.name] = command

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

    async def register_channel(self, uid: int, name: str):
        '''Registers a channel to the database if new, otherwise raises
        `RegistrationError`. This must only be called by a command sent
        in the bot's channel.'''

        if int(uid) in self._channels:
            error = f"Channel {name!r} is already registered."
            # raise RegistrationError(error)
            print(error)
            return

        print("Registering:", uid, name)
        channel = RegisteredChannel(uid, name, bot=self)
        self._channels[channel.id] = channel
        fields = ('id', 'name', 'join_date')
        values = (channel.id, channel.name, channel.join_date)
        # opt = ""
        opt = "or replace"
        _sql = f"insert {opt} into channel({','.join(fields)}) values (?,?,?)"
        try:
            self._db.execute(_sql, values)
        except sqlite3.Error as exc:
            self._channels.pop(uid)
            raise DatabaseError(exc.args[0])

    async def register_initial_channels(self):
        # assert hasattr(self, '_initial_channels')
        # Register the bot:
        await self.register_channel(self.user_id, self.display_name.lower())
        for channel in self.connected_channels:
            chan = await channel.user()
            await self.register_channel(chan.id, channel.name)
 
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

    async def resolve_long_alias(self, context: Context) -> tuple[CustomCommand|BuiltInCommand, str]:
        channel = context.channel
        content = context.message.content.lower()
        # print(content)
        # print(channel._alias_lookup.items())
        # for item in channel._alias_lookup.items():
        # cmds = channel.custom_command_aliases.items()
        # bins = channel.built_in_aliases.items()
        # default = self._built_in_command_aliases.items()
        # lookup = itertools.chain(cmds, bins, default)
        # # lookup = channel.custom_command_aliases
        lookup = channel._alias_lookup
        if lookup:
            # for alias, cmd in lookup.items():
            for alias, cmd in lookup:
                # print(f"{alias=}")
                # print(f"{cmd=}")
                if content.startswith(alias):
                    return alias, cmd
        return (None, None)

        # for alias, cmd in channel._alias_lookup.items():
            # print("alias:", alias)
            # print("cmd:", cmd)
            # if message.lower().startswith(alias):
                # return item
                # return cmd, alias


    async def get_command(self, context: Context) -> CustomCommand|BuiltInCommand:
        channel = context.channel
        command_name = context.message.content.partition(" ")[0]
        ci_name = command_name.lower()
        command = (
            channel.custom_command_aliases.get(ci_name)
            or channel.built_in_aliases.get(ci_name)
            or self._built_in_command_aliases.get(ci_name)
       )

        alias = None
        while command is None:
        #if command is None:
            alias, command = await self.resolve_long_alias(context)
            # match = await self.resolve_long_alias(context)
            #if match is not None:
                # alias, command = match
            # return
            #context.invoked_with = alias

        #if command is None:
            #context.invoked_with = None
            # context.is_valid = False  # Only useful for commands, not keywords.
            return

        context.invoked_with = command_name if alias is None else alias

        # else:
            # context.invoked_with = command_name

        bot_allows_cs = self.cfg.commands['channels_set_case']
        bot_default_cs = self.cfg.commands['defaults']['case_sensitive']
        # channel_cs = channel.case_sensitive
        command_cs = command.case_sensitive

        if bot_allows_cs:
            # if not (channel_cs or command_cs):
            if not command_cs:
                return command
        if not bot_default_cs:
            return command

        command = (channel._command_aliases.get(command_name) or
                   channel._built_in_aliases.get(command_name))
        return command


    #async def get_command(self, context: Context) -> CustomCommand|BuiltInCommand:
    #    channel = self._channels[context.channel.id]
    #    command_name = context.message.content.partition(" ")[0].lower()

    #    command = (channel.command_aliases.get(command_name) or
    #               channel.built_in_aliases.get(command_name))
    #    if command is None:

    #    if (channel.case_sensitive and channels_set_case) or bot_case_sensitive
    #    channel.aliasesandb.get(command_name)
    #        #  if the command is case-sensitive:
    #        #  which command?
    #    # if channel.case_sensitive:
    #        # command_name = command_or_alias 
    #    # else:
    #        # command_name = command_or_alias.lower()

    #    command = None
    #    if command_name in channel._command_aliases:
    #        #command = channel._commands[channel._command_aliases[command_name]]
    #        command = channel._command_aliases.get(command_name, None)
    #    elif command_name in channel._built_in_command_aliases:
    #        command = channel._built_ins.get(command_name, None)
    #    #elif command_name in self._built_in_command_aliases:

    #    return command

    async def get_built_in(self, name: str):
        command = self._built_in_command_aliases.get(name, None)

    async def get_context(self, message: Message) -> Context:
        '''Returns a `Context` object made from a `Message` returned by
        `event_message` after setting its attributes.'''
        context = Context(bot=self, message=message)
        return context

    async def handle_commands(self, context: Context):
        # print(vars(context))
        # context.prefix = "!"  # Remove after fixing cmd management

        content = context.message.content
        # command_name = content.partition(" ")[0]
        # command = await context.channel.resolve_command(command_name)
        alias = None
        # cmds_and_built_ins = zip(channel._command_aliases, self._built_in_command_aliases.items():
        command = await self.get_command(context)

        if command is not None:
            context.command = command

        context.msg_body = content.removeprefix(context.invoked_with).strip() if (
            context.invoked_with is not None) else content.strip()
        # if context._command_name in self._built_in_command_aliases:
            # return await self.built_in_commands[context.command](context)

        # print(f"{context.command = }")
        # print(f"{context.invoked_with = }")
        # print(f"{context.msg_body = }")

        if context.command is not None : #  or context.is_valid is not False:
            await context.command(context)
            # print(f"Command {context.command!r} should have run.")
            return 1


    async def handle_keywords(self, context: Context):
        #print(f"Got keyword in message {context.message.content!r}")
        pass


    async def event_ready(self):
        '''Have the bot do things upon connection to the Twitch server.'''
        print(f"{self.display_name} ({self.user_id}) is online!")

        await self.register_initial_channels()
        # print("Registered initial channels.")
        print("Registered channels:", self._channels)

        # Post a message in each registered channel's chat upon connection:
        # for channel in self.connected_channels:
        # notify = f"{self.display_name} is online!"
        #     await self.get_channel(channel).send(msg)
        #     pass

    async def event_message(self, message: Message):
        if message.echo:
            return
        # print(self._channels)
        #print(message.raw_data)
        # self.MESSAGE = message
        context = await self.get_context(message)
        self.CTX = context
        # import pickle
        # with open('bot.pkl', 'w') as f:
            # pickle.dump(self, f)
        # print(f"{context.channel.name} -> {context.message.content}")
        print(f"{context.author.name} -> {context.message.content}")
        # print(context.channel._command_aliases)
        command_ran = await self.handle_commands(context)
        if command_ran is not True:
            await self.handle_keywords(context)

