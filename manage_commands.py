from base_classes import Context
from errors import *


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
