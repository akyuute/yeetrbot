'''Functions for parsing config files, values and command strings.'''

from argparse import ArgumentParser, Namespace, ArgumentError
from errors import ParsingIncomplete, InvalidArgument, InvalidSyntax


class QuietParser(ArgumentParser):
    '''An `ArgumentParser` that doesn't spam stderr with usage messages.'''
    # def __init__(self, **kwargs):
        # super().__init__(self, **kwargs)

    def error(self, message):
        raise ParsingIncomplete(message)


parser = QuietParser(prog='!cmd', description='CMD DESC', exit_on_error=False)
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
# cmd_add_or_edit.add_argument('--override_builtin', action='store_true')

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


def parse_cmd(msg: str, parser: QuietParser = parser) -> tuple|Namespace:
    '''Parses a !cmd argument string, returning new data and message.'''
    args = msg.split()
    # error_preface = f"Failed to {args[0]} command {args[1]!r}."

    if len(args) < 3:
        if '-h' in args or '--help' in args:
            return parser.print_help()
        err = "Syntax error: Not enough arguments."
        cmd = args[1] if len(args) >= 2 else ""
        raise InvalidSyntax(err, cmd)

    num_parsed = 1
    last_result: Namespace = None
    valid_flags = ('--help', '-h', '--permissions', '-p', '--aliases', '-a',
                   '--count', '-c', '--hidden', '-i', '--disable', '-d')
    if args[0] == 'edit':
        valid_flags += ('--rename', '-r', '--enable', '-e', '--unhidden', '-u')

    for i, _ in enumerate(args):
        try:
            # Go ahead and parse the command if it is the minimum length:
            if len(args) == 3 and args[-1] in valid_flags:
                return parser.parse_args(args)
            last_result = parser.parse_args(args[:i+1])
            num_parsed += 1
        except ParsingIncomplete as exc:
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
                err = "Invalid argument: "
                raise InvalidArgument(err + repr(args[i]), args[1])

        except ArgumentError as exc:
            # If the command lacks a message, begins with anything that can be interpreted
            # as a flag, it will be considered a syntax error:
            #if args[i] not in valid_flags:
            #i == len(args) - 1
            if i == len(args) - 1 or args[i] not in valid_flags:
                err = "Syntax error: "
                raise InvalidSyntax(err + str(exc).capitalize(), args[1])
            num_parsed += 1

    if not last_result:
        num_parsed += 1
    # Do not attempt to include the message if every
    # argument in the command was parsed successfully:
    if len(args) == num_parsed:
        return last_result
    return last_result, msg.split(None, num_parsed)[-1]

