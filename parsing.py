'''Functions for parsing config files, values and command strings.'''

import argparse
from utils import split_nth, join_with_or
from errors import ParsingError, InvalidArgument


CMD_ARGUMENT_FLAGS = (
       '--permissions', '-p',
       '--aliases', '-a',
       '--count', '-c', 
       '--cases', '-i',
       '--no-cases', '-I',
       '--disable', '-d',
       '--enable', '-e',
       '--hide', '--unhide')

GROUP_DELIMITERS = "()[]{}<>\"\"''"

class QuietParser(argparse.ArgumentParser):
    '''An `ArgumentParser` that doesn't spam stderr with usage messages.'''
    def error(self, message):
        raise ParsingError(message)

class GroupByDelimiter(argparse.Action):
    '''Setting `action=GroupByDelimiter` makes an argument parse words found
    within delimiters like `()[]{}<>` and quotes together as a group.
    All leftover args are stored to the namespace attribute `leftover`.
    These args are the command message except when the argument is followed by
    other optional arguments.
    NOTE:
    nargs different from '+' risk data loss and may break the way other args
    are parsed.
    If you still wish to require a specific number of args, it may be wise to
    document the requirement in syntax and help messages so users are informed.
    '''
    def __init__(self, option_strings, dest, nargs='+', **kwargs):
        # NOTE:
        # nargs different from '+' risk data loss and may break the way other
        # args are parsed.
        # If you still wish to require a specific number of args,
        # inform users about the requirement. Data could be lost otherwise.

        # kwargs['nargs'] = '+'
        # Optionally raise an exception when it is set to anything else:
        # if nargs != '+':
            # e = (f"Argument {self.slash_names} 'nargs' parameter must be '+' "
                 # f"when action={self.__class__.__name__}")
            # raise ValueError(e)

        self.slash_names = "/".join(option_strings)
        try:
            self.delimiters = kwargs.pop('delimiters')
        except KeyError:
            error = (f"Argument {option_strings[0]!r} needs 'delimiters' "
                     f"parameter with action={self.__class__.__name__}.")
            raise ValueError(error)
        super().__init__(option_strings, dest, nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        argstr = " ".join(values)
        # Argument is the last item in the args list
        if len(values) == 1 and not namespace.message:
            return setattr(namespace, self.dest, argstr.strip(self.delimiters))

        try:
            i = self.delimiters.index(argstr[0])
        except ValueError:
            delim_opts = join_with_or(tuple(split_nth(self.delimiters, 2)))
            e = (f"The {self.slash_names!r} argument must be escaped with "
                 f"{delim_opts} when it is longer than one word or followed "
                 f"by other arguments.")
            e = " ".join(line.strip() for line in f"""
                The {self.slash_names!r} argument must be escaped with
                {delim_opts} when it is longer than one word or followed by
                other arguments.""".splitlines())
            # raise InvalidArgument(" ".join(line.strip() for line in e.splitlines()))
            raise InvalidArgument(e)

        start, end = self.delimiters[i:][:2]
        if start == end:  # For delimiters that are quotes
            _, arg, *leftover = argstr.split(end)
        else:
            arg, *leftover = argstr.split(end)

        # print(arg)
        # print(rest)
        setattr(namespace, self.dest, arg.removeprefix(start))
        setattr(namespace, 'leftover', end.join(leftover))
        

cmd_add_or_edit = QuietParser(prog='!cmd',
    add_help=False)
cmd_add_or_edit.set_defaults(
    default=None,
    is_enabled=None,
    is_hidden=None,
    )

cmd_add_or_edit.add_argument('--help', '-h',
        action='store_true',
        default=argparse.SUPPRESS)

cmd_add_or_edit.add_argument('--perms', '-p',
    choices="everyone vip moderator owner rank=".split(),
    type=lambda s: s.lower())

cmd_add_or_edit.add_argument('--aliases', '-a', nargs=1)
cmd_add_or_edit.add_argument('--count', '-c', type=int)

cmd_add_or_edit.add_argument('--case-sensitive', '-I',
    )

cmd_add_or_edit.add_argument('--disable', '-d',
    action='store_false',
    dest='is_enabled')

cmd_add_or_edit.add_argument('--enable', '-e',
    action='store_true',
    dest='is_enabled')

cmd_add_or_edit.add_argument('--hide',
    action='store_true',
    dest='is_hidden')

cmd_add_or_edit.add_argument('--unhide',
    action='store_false',
    dest='is_hidden')

cmd_add_or_edit.add_argument('--expire', '-x',
    action=GroupByDelimiter,
    delimiters=GROUP_DELIMITERS)

# cmd_add_or_edit.add_argument('--expire-at',
    # action=GroupByDelimiter,
    # delimiters=GROUP_DELIMITERS)

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

