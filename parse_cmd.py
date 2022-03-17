import argparse

parser = argparse.ArgumentParser(prog='!cmd', description='CMD DESC', exit_on_error=False)

subparsers = parser.add_subparsers(help="Help for all subcommands here.")

cmd_add_or_edit = subparsers.add_parser('!cmd', add_help=False)

# cmd_edit.set_defaults(func=edit)
cmd_add_or_edit.add_argument('command', nargs=1)
cmd_add_or_edit.add_argument('--permissions', '-p', choices="everyone rank= moderator vip owner".split())
cmd_add_or_edit.add_argument('--aliases', '-a', nargs=1)
cmd_add_or_edit.add_argument('--count', '-c', type=int)
cmd_add_or_edit.add_argument('--enable', action='store_true', dest='is_enabled')
cmd_add_or_edit.add_argument('--disable', action='store_false', dest='is_enabled')

cmd_add = subparsers.add_parser('add', aliases=('a', '+'), parents=[cmd_add_or_edit], exit_on_error=False, description="Add a new custom command.", help="ADD HELP")
cmd_edit = subparsers.add_parser('edit', aliases='e', parents=[cmd_add_or_edit], exit_on_error=False, description="Edit a custom command's message and properties.", help="EDIT HELP")
cmd_edit.add_argument('--rename', '-r', nargs=1)

other_cmd_actions = subparsers.add_parser('!cmd', add_help=False)
other_cmd_actions.add_argument('command', nargs='+')

cmd_delete = subparsers.add_parser('delete', parents=[other_cmd_actions], aliases=('remove',), exit_on_error=False, description="Delete commands.", help="Multiple commands may be deleted at once.")
cmd_disable = subparsers.add_parser('disable', parents=[other_cmd_actions], exit_on_error=False, description="Disable commands.", help="Multiple commands may be disabled at once.")
cmd_enable = subparsers.add_parser('enable', parents=[other_cmd_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")
# cmd_ = subparsers.add_parser('enable', parents=[other_cmd_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")

class InvalidArgument(Exception): ...
class InvalidSyntax(Exception): ...

def parse_cmd_add_edit(action, parser: argparse.ArgumentParser, msg: str):
    if len(msg) > 2:
        args = msg.split()
    else:
        return 2, None, ""
    num_args = 3
    last_result: argparse.Namespace = None
    flags = ('--permissions', '-p', '--aliases', '-a', '--count', '-c', '--enable', '--disable')
    if action == 'edit':
        flags += ('--rename',)
    for i, _ in enumerate(args):
        if i < 3:
            continue
        if args[i] in flags:
            please_parse = args[:i+2]
        else:
            please_parse = args[:i+1]
        try:
            last_result = parser.parse_args(please_parse)
            num_args += 1
        except argparse.ArgumentError as exc:
            return InvalidSyntax(f"ctx.user.mention(): Syntax error: {exc}")
        except SystemExit as exc:
            if args[i-2] in flags:
                # print("SUCCESSFUL")
                return None, last_result, msg.split(None, num_args)[-1]
            else:
                return InvalidArgument(f"ctx.user.mention(): Unrecognized argument: {args[i-1]!r}")
    return 0, last_result, msg.split(None, num_args)[-1]


# msg = "--help"
msg = "add !mycomm -p vip -c f 6 -a sdc,asdc fooo"
# msg = "edit asdc --asdc"
print(parse_cmd_add_edit('edit', parser, msg))
# parser.parse_args(msg.split())