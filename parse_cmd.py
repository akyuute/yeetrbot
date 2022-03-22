import argparse

parser = argparse.ArgumentParser(prog='!cmd', description='CMD DESC', exit_on_error=False)

subparsers = parser.add_subparsers(help="Help for all subcommands here.")

cmd_add_or_edit = subparsers.add_parser('!cmd', add_help=False)
cmd_add_or_edit.set_defaults(is_enabled=None)

cmd_add_or_edit.add_argument('command', nargs=1)
cmd_add_or_edit.add_argument('--permissions', '-p', choices="everyone rank= moderator vip owner".split())
cmd_add_or_edit.add_argument('--aliases', '-a', nargs=1)
cmd_add_or_edit.add_argument('--count', '-c', type=int)
cmd_add_or_edit.add_argument('--hide', '-i', action='store_true', dest='is_hidden')
cmd_add_or_edit.add_argument('--disable', '-d', action='store_false', default=None, dest='is_enabled')
# cmd_add_or_edit.add_argument('--invisible', '-i', action='store_true', dest='is_hidden')

cmd_add = subparsers.add_parser('add', parents=[cmd_add_or_edit], exit_on_error=False, description="Add a new custom command.", help="ADD HELP")
#cmd_add.set_defaults(is_enabled=True)

cmd_edit = subparsers.add_parser('edit', parents=[cmd_add_or_edit], exit_on_error=False, description="Edit a custom command's message and properties.", help="EDIT HELP")
# cmd_edit.set_defaults(func=edit)
#cmd_edit.set_defaults(is_enabled=None)

cmd_edit.add_argument('--unhide', '-u', action='store_false', dest='is_hidden')
# cmd_add_or_edit.add_argument('--visible', '-v', action='store_false', dest='is_hidden')
cmd_edit.add_argument('--rename', '-r', nargs=1, dest='new_name')
cmd_edit.add_argument('--enable', '-e', action='store_true', dest='is_enabled')

other_cmd_actions = subparsers.add_parser('!cmd', add_help=False)
other_cmd_actions.add_argument('command', nargs='+')

cmd_delete = subparsers.add_parser('delete', parents=[other_cmd_actions], aliases=('remove',), exit_on_error=False, description="Delete commands.", help="Multiple commands may be deleted at once.")
cmd_disable = subparsers.add_parser('disable', parents=[other_cmd_actions], exit_on_error=False, description="Disable commands.", help="Multiple commands may be disabled at once.")
cmd_enable = subparsers.add_parser('enable', parents=[other_cmd_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")
# cmd_ = subparsers.add_parser('enable', parents=[other_cmd_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")

class InvalidArgument(Exception): ...
class InvalidSyntax(Exception): ...


def parse(parser: argparse.Namespace, msg: str):
    '''Parses a !cmd add or !cmd edit command
    and returns new data and message.'''
    args = msg.split()
    if len(args) < 3:
        if '-h' in args or '--help' in args:
            return parser.print_help()
        return f"Syntax Error: Not enough arguments. <!cmd syntax info>"
    num_parsed = 1
    last_result: argparse.Namespace = None
    valid_flags = ('--help', '-h', '--permissions', '-p', '--aliases', '-a', '--count', '-c', '--hide', '-i', '--disable', '-d',  )
    if args[0] == 'edit':
        valid_flags += ('--rename', '-r', '--enable', '-e', '--unhide', '-u', )

    for i, _ in enumerate(args):
        try:
            # Go ahead and parse the command if it is the minimum length:
            if len(args) == 3 and args[-1] in valid_flags:
                return parser.parse_args(args)
            last_result = parser.parse_args(args[:i+1])
            num_parsed += 1
        except SystemExit as exc:
            # Catch the help flag:
            if args[i] in ('--help', '-h'):
                return parser.print_help()
            # Is the next pair of args invalid, meaning the beginning of the message?
            if not any(a in valid_flags for a in args[i+1:i+3]):
                # Disregard if this is just the command name:
                if i < 3:
                    continue
                break
            # If not a legitimate command name, catch this as an invalid arg:
            if i > 2:
                return InvalidArgument(f"Invalid argument: {args[i]!r}")

        except argparse.ArgumentError as exc:
            # If the command lacks a message, begins with anything that can be interpreted
            # as a flag, it will be considered a syntax error:
            #if args[i] not in valid_flags:
            #i == len(args) - 1
            if i == len(args) - 1 or args[i] not in valid_flags:
                return InvalidArgument(f"Syntax error: {exc}")
            num_parsed += 1

    if not last_result:
        num_parsed += 1
    # Do not attempt to include the message if every
    # argument in the command was parsed successfully:
    if len(args) == num_parsed:
        return last_result
    return last_result, msg.split(None, num_parsed)[-1]

