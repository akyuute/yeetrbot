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


def parse(parser, msg):

    args = msg.split()
    if len(args) < 3:
        return f"Syntax Error: Not enough arguments. <!cmd syntax info>"
        
    num_args = 1
    last_result: argparse.Namespace = None
    valid_flags = ('--permissions', '-p', '--aliases', '-a', '--count', '-c', '--hide', '-i', '--disable', '-d',  ) # '--invisible', '-i')
    if args[0] == 'edit':
        valid_flags += ('--rename', '-r', '--enable', '-e', '--unhide', '-u', ) # '--visible', '-v')

    # print(args)
    for i, _ in enumerate(args):
        #if i < 3:
            #continue
        # print(i, args[i])



        try:
            if len(args) == 3 and args[-1] in valid_flags:
                return parser.parse_args(args)
            last_result = parser.parse_args(args[:i+1])
            num_args += 1

        except SystemExit as exc:
            # print("SysEx")
            #print(last_result)
            # Is the next thing not a valid arg, meaning the beginning of the message?
            if not any(a in valid_flags for a in args[i+1:i+3]):
                print("!!! No flags in next 2 words")
                if i < 3:
                    print("Continuing...")
                    continue
                break
                #print(args[i])
                # if args[i] in valid_flags:
                    # print(args[i], "is a flag")
                    #num_args += 1
                #return last_result, msg.split(None, num_args)[-1]
            # if args[i+1] in valid_flags:
                # print("Found a flag in next arg...")
                # continue
            elif i > 3:
                # print("Next arg is not a valid flag...")
                return InvalidArgument(f"Unrecognized argument: {args[i]!r}")

        except argparse.ArgumentError as exc:
            # print("ArgErr")
            if args[i] not in valid_flags:
                return InvalidSyntax(f"Syntax error: {exc}")
            #elif i == len(args) - 1:
                #return exc
            if i == len(args) - 1 or args[i] not in valid_flags:
                return InvalidArgument(f"Syntax error: {exc}")
            num_args += 1

    # if not (num_args == len(args) and args[num_args] in valid_flags):
    # print("End of loop")
    # print(f"{num_args=}, {len(args)=}")
    if not last_result:
        num_args += 1
    if len(args) == num_args:
        return last_result
    return last_result, msg.split(None, num_args)[-1]

