import argparse

def edit(*args):
    # print(args)
    namespace, message = args[0]
    print(namespace.__dict__)
    print(' '.join(message))
    print("Function 'edit' ran.")

parser = argparse.ArgumentParser(prog='!commands', description="Manage channel commands from chat.", exit_on_error=False)
subparsers = parser.add_subparsers()

cmd_edit = subparsers.add_parser('edit', aliases='e', description="Edit a custom command's properties.", help="EDIT HELP",  exit_on_error=False)
cmd_edit.set_defaults(func=edit)
cmd_edit.add_argument('command', nargs='+', ) # help="HELP") # dest='command_name')
cmd_edit.add_argument('--permissions', '-p', choices="everyone rank= moderator vip owner".split(), dest='perms') # required=True)
cmd_edit.add_argument('--aliases', '-a', nargs=1 ) # nargs='+')
cmd_edit.add_argument('--count', '-c', type=int, required=False)
cmd_edit.add_argument('--is_enabled', choices="true t 1 false f 0".split(), required=False)
cmd_edit.add_argument('--enable', '-e', action='store_true', dest='is_enabled')
cmd_edit.add_argument('--disable', '-d', action='store_false', dest='is_enabled')
cmd_edit.add_argument('message', nargs='*', )
valid_flags = ('', 'command', '-p', '--enable')

# command_str = "edit foo1 \\-t foo2 -c 4 my   <3-space-gap> message is here." # --permissions moderator"
# command_str = "edit \"foo \\\" \\-p bar\" -p foo vip -c 3 --o unrec --enable a very long, \" '' \\ \\\\weird message" # --permissions moderator"
command_str = "edit foo bar baz"

# enum = enumerate(list(command_str))
# enum = enumerate(command_str.replace('  ', '   ').split(' '))
# pairs = [pair for pair in enum if pair[1] != '']
# print(' '.join(command_str.casefold().split()))
# print(list(enumerate(command_str.split())))
# print(pairs)


class InvalidArgument(Exception): ...

def test_args(parser, command_str):
    errs = []
    extras_len = 0
    args = command_str.split()
    parser_dict = {}
    for i, _ in enumerate(args):
        if i < 3:
            continue
        elif args[i-1] in valid_flags:
            # i += 1
            continue
        try:
            parsed_args = parser.parse_known_args(args)
            if len(parsed_args[1]) == extras_len:
                extras_len = len(parsed_args[1])
                raise InvalidArgument("ERROR", parser.parse_known_args(args))
            elif parser_dict != vars(parsed_args[0]):
                parser_dict = vars(parsed_args[0])
                parser.parse_args(args)
        except InvalidArgument as exc:
            return "INVALID", exc.args
        except argparse.ArgumentError as exc:
            errs.append(exc)
            print(exc)
            return
            # continue
            # print(vars(exc.args[0]))
            # return exc.__str__()
        except SystemExit:
            print("Got SystemExit error")
    if errs:
        # return errs[-1]
        return len(errs), errs
    else:
        args = command_str.strip().split(' ')
        return parser.parse_known_args(args)
        # print(parser.parse_args(args))
        return "No errors"



# def test_args(parser: argparse.ArgumentParser, command_str):
#     excs = []
#     extras_len = 0
#     args = command_str.split(' ')
#     parser_dict = {}
#     for i, arg in enumerate(args):
#         if i < 2:
#             continue
#         if args[i] in valid_flags:
#             # print(args[i-1])
#             i += 1
#             # continue
#         try:
#             parsed_args = parser.parse_known_args(args[:i])
#             # print(parsed_args)
#             if len(parsed_args[1]) == extras_len:
#                 extras_len = len(parsed_args[1])
#             elif parser_dict != vars(parsed_args[0]):
#                 parser_dict = vars(parsed_args[0])
#                 error = f"ctx.author.mention(): Invalid argument: {args[i-1]!r} Usage: {parser.format_usage()}"
#                 return error
#                 # raise InvalidArgument(f"ctx.author.mention(): Invalid argument: {args[i-1]!r} Usage: {parser.format_usage()}")
#                 # raise InvalidArgument(error)

#                 # return f"(Iteration {i}; INVALID ARG: {args[i-1]}"
#                 # print(f"(Iteration {i}; INVALID ARG: {args[i-1]}")
#                 # print(arg)
#                 # print("Invalid argument:", args[i-1])
#                 # print(parsed_args)
#                 # return parser.parse_known_args(args[:i-1])
#                 # print(parser.parse_args(args[:i]))
#                 # return parser.print_usage()
#                 # return
#         except InvalidArgument as exc:
#             # return exc.args[0]
#         # except Exception as exc:
#             # excs.append(exc)
#             return exc.args[0]
#             # # raise parser.
#             # # raise parser.error("SDFNSDC")
#             # continue

#         except argparse.ArgumentError as exc:
#             excs.append(parser.parse_args(args))
#             continue
#         #     # return exc.args[0]
#         #     # return parser.parse_args(args)
#         #     # print(parser.parse_args(args))
#             # pass

#         # except SystemExit as exc:
#             # excs.append(exc)
#             # continue
#         #     # return exc
#         #     # return parser.parse_args(args)
#         #     # pass

#         # finally:
#     # return excs[-1].__str__()
#     return [err.__str__() + "\n" for err in excs]

            # if excs:
                # print(excs[-1])
            # else: return "welp"
    # print(excs[-1].__str__())
    # print(argparse.ArgumentError.__dict__)
    # print(dir(excs[0]))
    # print([dir(thing) for thing in excs[0].__dict__.values()])
    # print(excs[0].format_usage())
    # return f"ctx.author.mention(): {excs[-1]} {parsed_args}"
    # return "soicn"


print( test_args(parser, "edit aco kj kjh -c 6  awfec -a bar,far adsv"))
# print(len(str(parser._subparsers.__dict__)))
# print(parser._subparsers.__dict__['_group_actions'][0].choices)

# {'description': None, 'argument_default': None, 'prefix_chars': '-', 'conflict_handler': 'error', '_registries': {'action': {None: <class 'argparse._StoreAction'>, 'store': <class 'argparse._StoreAction'>, 'store_const': <class 'argparse._StoreConstAction'>, 'store_true': <class 'argparse._StoreTrueAction'>, 'store_false': <class 'argparse._StoreFalseAction'>, 'append': <class 'argparse._AppendAction'>, 'append_const': <class 'argparse._AppendConstAction'>, 'count': <class 'argparse._CountAction'>, 'help': <class 'argparse._HelpAction'>, 'version': <class 'argparse._VersionAction'>, 'parsers': <class 'argparse._SubParsersAction'>, 'extend': <class 'argparse._ExtendAction'>}, 'type': {None: <function ArgumentParser.__init__.<locals>.identity at 0x7fdd64f736d0>}}, '_actions': [_HelpAction(option_strings=['-h', '--help'], dest='help', nargs=0, const=None, default='==SUPPRESS==', type=None, choices=None, help='show this help message and exit', metavar=None), _SubParsersAction(option_strings=[], dest='==SUPPRESS==', nargs='A...', const=None, default=None, type=None, choices={'edit': ArgumentParser(prog='!commands edit', 0=None, description="Edit a custom command's properties.", formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True), 'e': ArgumentParser(prog='!commands edit', usage=None, description="Edit a custom command's properties.", formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True)}, help=None, metavar=None)], '_option_string_actions': {'-h': _HelpAction(option_strings=['-h', '--help'], dest='help', nargs=0, const=None, default='==SUPPRESS==', type=None, choices=None, help='show this help message and exit', metavar=None), '--help': _HelpAction(option_strings=['-h', '--help'], dest='help', nargs=0, const=None, default='==SUPPRESS==', type=None, choices=None, help='show this help message and exit', metavar=None)}, '_action_groups': [], '_mutually_exclusive_groups': [], '_defaults': {}, '_negative_number_matcher': re.compile('^-\\d+$|^-\\d*\\.\\d+$'), '_has_negative_number_optionals': [], 'title': 'positional arguments', '_group_actions': [_SubParsersAction(option_strings=[], dest='==SUPPRESS==', nargs='A...', const=None, default=None, type=None, choices={'edit': ArgumentParser(prog='!commands edit', usage=None, description="Edit a custom command's properties.", formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True), 'e': ArgumentParser(prog='!commands edit', usage=None, description="Edit a custom command's properties.", formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True)}, help=None, metavar=None)]}

# test_args(parser, command_str)


# args = cmd_edit.parse_known_intermixed_args(command_str.split(' '))
# args = parser.parse_args(command_str.split(' '))
# print(len(command_str))
# print(f"Original msg:\n{command_str}\nCommand message after parsing:\n{' '.join(args[-1]):>49}")
# args[0].func(dict(zip(['args', 'message'], args)))

# args[0].func(args)

# print(args)
