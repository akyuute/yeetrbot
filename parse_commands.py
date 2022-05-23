from abcs import Bot
from typing import Dict, Tuple
import time
from base_classes import Config, Context, RegisteredChannel, CustomCommand, BuiltInCommand
from parsing import (cmd_add_parser, cmd_edit_parser,
    CMD_ARGUMENT_FLAGS)
from errors import *
from textwrap import dedent

async def resolve_intent(
        bot: Bot,
        msg: str,
        cmd_name: str,
        base_cmd: Dict[str, str]
    ) -> Tuple[str, str]:
    body = msg.split(None, 1) if msg else ""
    if cmd_name == base_cmd['name'] and body:
        (action, msg) = body if len(body) > 1 else (body[0], "")
    else:  # If cmd_name is in alias_switch.values()...
        action = base_cmd['action_aliases'].get(cmd_name)
    return action, msg


# async def manage_commands(bot, ctx: Context):
async def manage_commands(bot, msg):
    '''Parses a `!cmd` string and executes `add_command()`, `edit_command()`,
    `toggle_command()` or `delete_command()` based on the implied action.'''

    cid = 1234
#    cid = ctx.channel.id
#    if cid not in bot._channels:
#        error = f"Channel with id {cid} is not registered."
#        raise ChannelNotFoundError(error)

#    cmd_name = ctx.command.name
    # bot.cfg.commands['core_built_ins']['manage_commands']['aliases']
    base_cmd = bot.cfg.commands['core_built_ins']['cmd_manage_commands']
    cfg = bot.cfg.commands
    
    #action, msg = get_intent(bot, ctx.
    fn_switch = base_cmd['fn_switch']
    actions = fn_switch.keys()

    # prefix_base = bot._base_command_name
    base_opts = "<command> [options ...]"
    base_usage = f"{base_cmd['name']} {{{' | '.join(actions)}}} {base_opts}"

    action = ""
#    msg = ctx.message.msg_body
    # msg = "add !foo -a !fooalias -ip vip Test message"

    if len(msg.split()) == 1:
        name, msg = (msg, "")
    else:
        name, msg = msg.split(None, 1) or (msg, "")

    action, msg = await resolve_intent(bot, msg, "!cmd", base_cmd)

    # if action in ('delete', 'disable', 'enable', 'alias'):
    if action in set(fn_switch.keys()) - set(('add', 'edit')):
        names = set(msg.split())
        if not names:
            error = f"""
            Invalid syntax. Please specify at least
            one valid command name to {action}."""
            raise InvalidSyntax(dedent(error))
        return fn_switch[action](cid, action, names)

    elif action not in actions:
        error = f"""
            Invalid action: {action!r}.
            """ # {ctx.cmd} usage: {base_usage!r}"""
        raise InvalidAction(dedent(error))

#    get_base_and_alias = lambda a: (
#        f"{prefix_base} {a}",
#        ctx.prefix + alias_switch[a])
#    base_and_alias = {a: get_base_and_alias(a) for a in ('add', 'edit')}
#    used_alias = prefixless in alias_switch.values()
#    base_or_alias = (
#        f"{prefix_base} {action}",
#        ctx.prefix + alias_switch.get(action, action))[used_alias]
    base_or_alias = msg.partition(" ")[0]

    msg_repr_fmts = ("[message]", "<message>")
    message_repr = msg_repr_fmts[cfg['require_message'] and action == 'add']
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
                LINE 99 after CMD_ARGUMENT_FLAGS"""

#                {base_and_alias[action][used_alias]} syntax:
#                {bot._get_syntax(action, args)}"""
#            return dedent(resp)
#            return usage
#        existing_or_new = ("an existing", "a new")[action == 'add']
        error =  f"""

            Invalid syntax. The first argument of
            {base_or_alias} must be {existing_or_new} command name."""
        raise InvalidSyntax(dedent(error))
    # elif not msg:
        # return usage

    error_preface = f"Failed to {action} command {name!r}"

    update_err_dict = {
        'add': [{
            'test': False,
            #'test': name in bot._channels[cid].commands,
            'exc': NameConflict(dedent(f"""
                {error_preface}.
                This command already exists. To change its message or
                properties, use 
                """))
                #{base_and_alias['edit'][used_alias]!r}."""))
            }, {

            'test': name in bot._built_in_command_aliases,
            'exc': NameConflict(dedent(f"""
                {error_preface}.
                Command name conflicts with a built-in command with the
                same name. Use '--override_builtin' if you want to replace
                it with your custom command. If you change your mind
                later, simply delete the custom command."""))
            },
        ],

        'edit': [{
            'test': False,
            #'test': name not in bot._channels[cid].commands,
            'exc': CommandNotFoundError(dedent(f"""
                {error_preface}.
                This command does not exist.
                """))
                # To add it, use {base_and_alias['add'][used_alias]!r}."""))
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
            {bot._get_syntax(action, args)}"""
        return dedent(resp)
        return usage


    cmd_dict.update(
        cid=cid,
        name=name,
        message= ' '.join(cmd_dict.get('message')) or None,
        action=action,
        # modified_by=ctx.author_id,
        modified_by = 1234,
        mtime=round(time.time()),
        base_or_alias=base_or_alias
    )
    print("cmd_dict: ", cmd_dict)

    for error in update_err_dict[action]:
        if error['test']:
            raise error['exc']

    if action in ('add', 'edit'):
        return fn_switch[action](cmd_dict)
    else:
        raise InvalidSyntax(f"Invalid syntax: {action!r}")

def add_command(bot, cmd_dict: dict):
    '''Adds a custom command to memory and the database.'''
    cmd_dict.setdefault('author_id', cmd_dict['modified_by'])
    cmd_dict.setdefault('perms', bot._default_perms)
    cmd_dict.setdefault('count', bot._default_count)
    cmd_dict.setdefault('cooldowns', bot._default_cooldowns)
    cmd_dict.setdefault('case_sensitive', bot._case_sensitive_commands)
    cid = cmd_dict['channel_id']
    name = cmd_dict['name']
    cmd_dict.pop('action')
    base_or_alias = cmd_dict.pop('base_or_alias')

    error_preface = f"Failed to add command {name!r}"
    error = ""

    if cmd_dict['message'] is None and bot._require_message:
        error = f"""
            {error_preface}.
            A message is required when adding a new command.
            Messages must come after any arguments."""
        raise RegistrationError(dedent(error))

    attrs = {k: v for k, v in cmd_dict.items() if v is not None}
    cmd = CustomCommand(**attrs)
    # print("cmd = ", dc.asdict(cmd))

    bot._channels[cid].commands[name] = cmd
    cols, vals = zip(*dc.asdict(cmd).items())
    plchd = ','.join(':' + str(c) for c in cols)
    _sql = f"insert into command ({','.join(cols)}) values ({plchd})"
    try:
        with bot._db_conn:
            bot._db.execute(_sql, vals)
    except sqlite3.Error as exc:
        error = f"{error_preface}. DatabaseError: {exc.args[0]}"
        raise DatabaseError(error)
    print("Added:", cmd)
    return f"Successfully added command {name}."

def edit_command(bot, cmd_dict: dict):
    '''Alters a custom command's properties in memory and the database.'''
    cid = cmd_dict['channel_id']
    commands = bot._channels[cid].commands
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

    # keys, vals = zip(*dc.asdict(cmd).items())
    cols = ','.join(cmd_dict.keys())
    params = ','.join(['?'] * len(cmd_dict))
    cond = f"(cid, name) = ({cid}, {name!r})"
    _sql = f"update command set({cols}) = ({params}) where {cond}"

    try:
        with bot._db_conn:
            # bot._db.execute(_sql, dc.astuple(cmd))
            bot._db.execute(_sql, tuple(cmd_dict.values()))
    except sqlite3.Error as exc:
        error = f"{error_preface}. Database error: {exc.args[0]}"
        raise DatabaseError(error)
    print("Edited:", bot._channels[cid].commands.get(name) or new_cmd)
    resp = f"Successfully updated command {name}"
    resp += f" and renamed it {new_name!r}." if new_name else "."
    return resp

def toggle_command(bot, cid, action: str, names: set):
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

def delete_command(bot, cid: int, action: str, names):
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
