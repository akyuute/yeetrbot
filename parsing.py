'''Functions for parsing config files, values and command strings.'''

import argparse
from errors import ParsingError

valid_parser_flags = ('--help', '-h', '--permissions', '-p', '--aliases', '-a',
       '--count', '-c', '--disable', '-d', '--hide', '-i', '--unhide', '-u')

class QuietParser(argparse.ArgumentParser):
    '''An `ArgumentParser` that doesn't spam stderr with usage messages.'''
    def error(self, message):
        raise ParsingError(message)


cmd_add_or_edit = QuietParser(prog='!cmd',
    add_help=False)
cmd_add_or_edit.set_defaults(default=None)

cmd_add_or_edit.add_argument('--help', '-h',
        action='store_true',
        default=argparse.SUPPRESS)

cmd_add_or_edit.add_argument('--perms', '-p',
    choices="everyone vip moderator owner rank=".split(),
    type=lambda s: s.lower())

cmd_add_or_edit.add_argument('--aliases', '-a', nargs=1)
cmd_add_or_edit.add_argument('--count', '-c', type=int)

cmd_add_or_edit.add_argument('--disable', '-d',
    action='store_false',
    dest='is_enabled')

cmd_add_or_edit.add_argument('--enable', '-e',
    action='store_true',
    dest='is_enabled')

cmd_add_or_edit.add_argument('--hide', '-i',
    action='store_true',
    dest='is_hidden')

cmd_add_or_edit.add_argument('--unhide', '-u',
    action='store_false',
    dest='is_hidden')

# cmd_add_or_edit.add_argument('--override_builtin', action='store_true')
cmd_add_or_edit.add_argument('message', nargs=argparse.REMAINDER)

cmd_add_parser = QuietParser('add', parents=[cmd_add_or_edit],
    description="Add a new custom command.",
    add_help=False
    )

cmd_edit_parser = QuietParser('edit', parents=[cmd_add_or_edit],
    description="Edit a custom command's message and properties.",
    add_help=False
    )
cmd_edit_parser.add_argument('--rename', '-r', nargs=1, dest='new_name')

