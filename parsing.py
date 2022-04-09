'''Functions for parsing config files, values and command strings.'''

from configparser import ConfigParser
from argparse import ArgumentParser, Namespace, ArgumentError


class InvalidArgument(Exception):
    '''Error raised when a parsed argument is counted as invalid.'''
    pass

class InvalidSyntax(Exception):
    '''Error raised when the syntax of a series of arguments is invalid.'''
    pass

class InvalidAction(Exception):
    '''Error raised when the first argument of a
    command string does not match a valid action.'''
    pass

def interpret_bool(value: str):
    truthy = "true t yes y on 1".split()
    falsy = "false f no n off 0".split()
    pattern = value.lower()
    if pattern not in truthy + falsy:
        raise ValueError(f"Invalid argument: {pattern!r}")
    match = pattern in truthy or not pattern in falsy
    return match


parser = ArgumentParser(prog='!cmd', description='CMD DESC', exit_on_error=False)
subparsers = parser.add_subparsers(help="Help for all subcommands here.")

cmd_add_or_edit = subparsers.add_parser('!cmd', add_help=False)
cmd_add_or_edit.add_argument('name', nargs=1)
cmd_add_or_edit.add_argument('--perms', '-p',
    choices="everyone vip moderator owner rank=".split(),
    type=lambda s: s.lower())
cmd_add_or_edit.add_argument('--aliases', '-a', nargs=1)
cmd_add_or_edit.add_argument('--count', '-c', type=int)
cmd_add_or_edit.add_argument('--disable', '-d', action='store_false', dest='is_enabled')
cmd_add_or_edit.add_argument('--hidden', '-i', action='store_true', dest='is_hidden')
cmd_add_or_edit.add_argument('--override_builtin', action='store_true')

cmd_add = subparsers.add_parser('add', parents=[cmd_add_or_edit], exit_on_error=False, description="Add a new custom command.", help="ADD HELP")

cmd_edit = subparsers.add_parser('edit', parents=[cmd_add_or_edit],
    exit_on_error=False,
    description="Edit a custom command's message and properties.",
    help="EDIT HELP")
cmd_edit.add_argument('--enable', '-e', action='store_true', dest='is_enabled')
cmd_edit.add_argument('--unhidden', '-u', action='store_false', dest='is_hidden')
cmd_edit.add_argument('--rename', '-r', nargs=1, dest='new_name')

other_actions = subparsers.add_parser('!cmd', add_help=False)
other_actions.add_argument('commands', nargs='+')

#cmd_delete = subparsers.add_parser('delete', parents=[other_actions], exit_on_error=False, description="Delete commands.", help="Multiple commands may be deleted at once.")
#cmd_disable = subparsers.add_parser('disable', parents=[other_actions], exit_on_error=False, description="Disable commands.", help="Multiple commands may be disabled at once.")
#cmd_enable = subparsers.add_parser('enable', parents=[other_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")
#cmd_alias = subparsers.add_parser('alias', parents=[other_actions], exit_on_error=False, description="Set command aliases.", help="Specify one or more aliases for a given command.")


def parse_cmd(msg: str, parser: ArgumentParser = parser) -> tuple|Namespace:
    '''Parses a !cmd argument string, returns new data and message.'''
    args = msg.split()
    if len(args) < 2:
        if '-h' in args or '--help' in args:
            return parser.print_help()
        raise InvalidSyntax("Syntax Error: Not enough arguments. <!cmd syntax info>")
    if args[0] in ('delete', 'enable', 'disable'):
        result = parser.parse_args(args)
        # print(f"{result=}")
        return result

    num_parsed = 1
    last_result: Namespace = None
    valid_flags = ('--help', '-h', '--permissions', '-p', '--aliases', '-a', '--count', '-c', '--hidden', '-i', '--disable', '-d',  )
    if args[0] == 'edit':
        valid_flags += ('--rename', '-r', '--enable', '-e', '--unhidden', '-u', )

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
            if set(valid_flags).isdisjoint(set(args[i+1:i+3])):
            #if not any(a in valid_flags for a in args[i+1:i+3]):
                # Disregard if this is just the command name:
                if i < 3:
                    continue
                break
            # If not a legitimate command name, catch this as an invalid arg:
            if i > 2:
                raise InvalidArgument(f"Invalid argument: {args[i]!r}")

        except ArgumentError as exc:
            # If the command lacks a message, begins with anything that can be interpreted
            # as a flag, it will be considered a syntax error:
            #if args[i] not in valid_flags:
            #i == len(args) - 1
            if i == len(args) - 1 or args[i] not in valid_flags:
                raise InvalidArgument(f"Syntax error: {exc.capitalize()}")
            num_parsed += 1

    if not last_result:
        num_parsed += 1
    # Do not attempt to include the message if every
    # argument in the command was parsed successfully:
    if len(args) == num_parsed:
        return last_result
    return last_result, msg.split(None, num_parsed)[-1]

