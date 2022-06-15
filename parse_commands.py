from base_classes import Config, Context, RegisteredChannel, CustomCommand, BuiltInCommand
from parsing import cmd_add_parser, cmd_edit_parser, CMD_ARGUMENT_FLAGS
from errors import *
from abcs import Bot
from utils import eprint

import time
import json
import sqlite3
import dataclasses
from textwrap import dedent
from typing import Dict, Tuple, Iterable


PARSED_ACTIONS = ('add', 'edit')
PARSER_SWITCH = {'add': cmd_add_parser, 'edit': cmd_edit_parser}


class Operation:
    def __init__(self, action: str, names: Iterable[str]):
        self.action = action
        self.names = set(names)


class ManageCmdParser:

##FN_SWITCH = {
##    'add': add_command,
##    'edit': edit_command,
##    'delete': delete_command,
##    'disable': toggle_command,
##    'enable': toggle_command,
##    #'alias': edit_command
##}

    def __init__(self, bot, command_config: dict = None):
        self.bot = bot
        self.config = command_config
        if command_config is None:
            self.config = bot.cfg.commands

        self.base_cmd = self.config['core_built_ins']['cmd_manage_commands']
        self.action_aliases = {
            v: k for k, v in self.base_cmd['action_aliases'].items()}
        actions = self.action_aliases.values()
        base_opts = "<command> [options ...]"
        self.base_usage = (
            f"{self.base_cmd['name']} "
            f"{{{' | '.join(actions)}}} {base_opts}"
        )

    @property
    def alias_switch(self):
        return {alias: act for act, alias in self.action_aliases.items()}

##    @property
##    def fn_switch(self):
##        return self.config['core_built_ins']['cmd_manage_commands']['fn_switch']

    def get_action(self, ctx):
        '''Returns the implied action of a command management invocation and
        the rest of the message. These depend on the literal action following
        the base command name or the alias used.'''
        body = ctx.msg_body

        if ctx.invoked_with == ctx.command.name:
            try:
                action, msg = body.split(None, 1)
            except ValueError:
                action = body
                msg = None
        else:
            action = self.action_aliases.get(ctx.invoked_with, None)
            msg = body.strip() or None

        return action, msg


    def manage_commands(self, ctx: Context):
        '''Parses a `!cmd` string and executes `add_command()`, `edit_command()`,
        `toggle_command()` or `delete_command()` based on the implied action.'''

        cfg = ctx.bot.cfg.commands
        base_cmd = self.base_cmd
        fn_switch = base_cmd['fn_switch']
        actions = self.action_aliases.values()
        # fn_switch = FN_SWITCH
        # print(self.alias_switch)

        if len(ctx.msg_body.split()) < 1:
            resp = f"{self.base_cmd['name']} usage: {self.base_usage!r}"
            raise CommandHelpMessage(resp)

        action, msg = self.get_action(ctx)

        # print(f"action: {action}, msg: {msg}")

        if action not in actions:
            error = f"""
                Invalid action for {self.base_cmd['name']}: {action!r}.
                {self.base_cmd['name']} usage: {self.base_usage!r}"""
            raise InvalidAction(dedent(error))

        if msg is None:
            resp =  f"{ctx.invoked_with} syntax: ..."
            # resp = "Imagine this is the syntax for whatever you're trying to do..."
            # raise CommandHelpMessage(resp)
            return resp

        if action not in PARSED_ACTIONS:
            names = set(msg.split())

            if not names:
                return f"{ctx.invoked_with} syntax: ..."
                error = f"""
                Invalid syntax. Please specify at least
                one valid command name to {action}."""
                raise InvalidSyntax(dedent(error))

            op = Operation(action, names)
            # return fn_switch[action](cid, action, names)
            return fn_switch[action](op)

        body = msg.split(None, 1)
        if len(body) == 0:
            name, msg = "", ""
        elif len(body) == 1:
            name, msg = msg, ""
        else:
            name, msg = body

        error_preface = f"Failed to {action} command {name!r}"
        base_opts = "<command> [options ...]"
        base_usage = f"{base_cmd['name']} {{{' | '.join(actions)}}} {base_opts}"

        args = msg.split(' ')
        parser = PARSER_SWITCH[action]

        try:
            parsed = parser.parse_args(args)
        except ParsingError as exc:
            raise ParsingError(f"{error_preface}. {exc.args[0].capitalize()}")

        cmd_dict = vars(parsed)

        if cmd_dict.get('help') is True:
            args = msg.split()
            print("Got --help in", repr(args))
            # args = (k for k, v in cmd_dict.items() if v is not None)
            # print(list(args))
            resp = f"""
                {ctx.invoked_with} syntax:
                {ctx.bot._get_syntax(action, args)}"""
            return dedent(resp)
            return usage


        for default in self.config['defaults'].items():
            cmd_dict.setdefault(*default)
        cmd_dict['name'] = name
        cmd_dict['message'] = ' '.join(cmd_dict.get('message')) or None
        # aliases = cmd_dict.pop('aliases')
        # cmd_dict['aliases'] = aliases[0].split(',') if len(aliases) else None
        # cmd_dict['alias_str'] = json.dumps(aliases)
        cmd_dict['modified_by'] = int(ctx.author.id)

        # print(f"{cmd_dict = }")

        return fn_switch[action](ctx, cmd_dict)


    # Consider moving these methods to Yeetrbot.
    # Have them accept CustomCommand objects instead of cmd_dict.
    # In this file, implement a create_command(), etc., which generate the commands.
    # For !delcmd, toggle_cmd, this may not be necessary. Simply passing the channel
    # id should be sufficient.
    # In any case, APIs that take Context and call these underlying methods would be
    # very helpful for error handling.

    def add_command(self, ctx: Context, cmd_dict: dict,
        config: dict = None
        # defaults: dict = None,
        ):
        '''Adds a custom command to memory and the database.'''
        if config is None:
            config = self.config
        # if defaults is None:
            # defaults = ctx.bot.cfg.commands['defaults']

        name = cmd_dict['name']
        error_preface = f"Failed to add command {name!r}"

        if name in ctx.channel._command_aliases:
            error = f"{error_preface}. Command {name!r} already exists."
            raise NameConflict(error)

        if cmd_dict['message'] is None and config.get('require_message'):
            error = f"""
                {error_preface}.
                A message is required when adding a new command.
                Messages must come after any arguments."""
            raise RegistrationError(dedent(error))

        cid = ctx.channel.id
        print(type(cid))
        cmd_dict.setdefault('author_id', cmd_dict.get('modified_by'))
        # cmd_dict['aliases'] = ','.join(cmd_dict.get('aliases', "")) or None
        cmd_dict['cooldowns'] = ','.join(cmd_dict.get('cooldowns', ""))

        attrs = {k: v for k, v in cmd_dict.items() if v is not None}
        # attrs['channel_id'] = cid
        print(f"{attrs = }")

        cmd = CustomCommand(**attrs, channel_id=cid)
        db_ready = dataclasses.asdict(cmd)
        # db_ready.pop
        aliases = db_ready.pop('aliases')
        db_ready['alias_str'] = json.dumps(aliases)
        # db_ready['aliases'] = ','.join(db_ready['aliases'])
        print(f"{db_ready = }")

        cols, vals = zip(*db_ready.items())
        # cols, vals = zip(*attrs.items())
        # print(f"{cols = }; {vals = }")
        plchd = ','.join(':' + str(c) for c in cols)

        _sql = f"insert into custom_command ({','.join(cols)}) values ({plchd})"
        try:
            # with ctx.bot._db_conn:
            ctx.bot._db.execute(_sql, vals)
        except sqlite3.Error as exc:
            error = f"{error_preface}. DatabaseError: {exc.args[0]}"
            raise DatabaseError(error)

        cmd = CustomCommand(**attrs, channel_id=cid)
        ctx.bot._channels[cid]._command_aliases[name] = cmd

        print("Added:", cmd)
        return f"Successfully added command {name}."

    def edit_command(self, ctx: Context, cmd_dict: dict):
        '''Alters a custom command's properties in memory and the database.'''
        cid = cmd_dict['channel_id']
        commands = bot._channels[cid].commands
        name = cmd_dict.pop('name')
        new_name = cmd_dict.pop('new_name')
        new_name = new_name[0] if isinstance(new_name, list) else None
        modified_by = cmd_dict
        # base_or_alias = cmd_dict.pop('base_or_alias')
        action = cmd_dict.pop('action')

        error_preface = f"Falied to update command {name!r}"
        error = ""

        if new_name in commands:
            error = f"""
                {error_preface}. Naming conflict: The name {new_name!r}
                matches another command with the same name.
                Please find a different new name for {name!r}."""
            raise NameConflict(dedent(error))
        elif new_name in bot.built_in_commands : # and not override_builtin:
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
                setattr(bot._channels[cid].commands[name], key, val)
            else:
                cmd_dict.pop(key)
        if new_name:
            cmd_dict['name'] = new_name
            new_cmd = bot._channels[cid].commands.pop(name)
            bot._channels[cid].commands[new_name] = new_cmd

        # keys, vals = zip(*dataclasses.asdict(cmd).items())
        cols = ','.join(cmd_dict.keys())
        params = ','.join(['?'] * len(cmd_dict))
        cond = f"(cid, name) = ({cid}, {name!r})"
        _sql = f"update command set({cols}) = ({params}) where {cond}"

        try:
            with bot._db_conn:
                # bot._db.execute(_sql, dataclasses.astuple(cmd))
                bot._db.execute(_sql, tuple(cmd_dict.values()))
        except sqlite3.Error as exc:
            error = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(error)
        print("Edited:", bot._channels[cid].commands.get(name) or new_cmd)
        resp = f"Successfully updated command {name}"
        resp += f" and renamed it {new_name!r}." if new_name else "."
        return resp

    def toggle_command(self, ctx: Context, op: Operation):
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
            if name not in bot._channels[cid].commands:
                error = f"{error_preface}. Command {name!r} does not exist."
                raise CommandNotFoundError(error)
            bot._channels[cid].commands[name].is_enabled = toggle

        cond = f"(cid, name) = ({cid}, ?)"
        _sql = f"update command set is_enabled = ? where {cond}"
        try:
            with bot._db_conn:
                bot._db.executemany(_sql, zip([toggle] * count, names))
        except sqlite3.Error as exc:
            error = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(error)

        desc = f"{count} command{plur}" if plur else f"command {names.pop()}"
        resp = f"Successfully {action}d {desc}."
        return resp

    def delete_command(self, ctx: Context, op: Operation):
        '''Delete a command, updating the database and in-memory dataclass.'''
        count = len(names)
        plur = "s" if count > 1 else ""
        error_preface = f"Failed to delete {count} command{plur}"
        error = ""

        for name in names:
            if name in bot._channels[cid].commands:
                del bot._channels[cid].commands[name]
            elif name in bot.built_in_commands:
                error = f"""
                    {error_preface}. Command {name!r} is a built-in command.
                    It cannot be deleted, but you may disable
                    it with '!disable {name}'."""
                raise NameConflict(dedent(error))
            else:
                error = f"{error_preface}. Command {name!r} does not exist."
                raise CommandNotFoundError(error)

        cond = f"(cid, name) = ({cid}, ?)"
        _sql = f"delete from command where {cond}"
        try:
            with bot._db_conn:
                bot._db.executemany(_sql, zip(names))
        except sqlite3.Error as exc:
            error = f"{error_preface}. Database error: {exc.args[0]}"
            raise DatabaseError(error)
        desc = f"{count} command{plur}" if plur else f"command {names.pop()}"
        resp = f"Successfully deleted {desc}."
        return resp
