import argparse

parser = argparse.ArgumentParser(prog='!cmd', description='CMD DESC', exit_on_error=False)

subparsers = parser.add_subparsers(help="Help for all subcommands here.")

cmd_add_or_edit = subparsers.add_parser('!cmd', add_help=False)

# cmd_edit.set_defaults(func=edit)
cmd_add_or_edit.add_argument('command', nargs=1)
cmd_add_or_edit.add_argument('--permissions', '-p', choices="everyone rank= moderator vip owner".split())
cmd_add_or_edit.add_argument('--aliases', '-a', nargs=1)
cmd_add_or_edit.add_argument('--count', '-c', type=int)
cmd_add_or_edit.add_argument('--hide', '-i', action='store_true', dest='is_hidden')
cmd_add_or_edit.add_argument('--disable', action='store_false', dest='is_enabled')
# cmd_add_or_edit.add_argument('--invisible', '-i', action='store_true', dest='is_hidden')

cmd_add = subparsers.add_parser('add', aliases=('a', '+'), parents=[cmd_add_or_edit], exit_on_error=False, description="Add a new custom command.", help="ADD HELP")
cmd_edit = subparsers.add_parser('edit', aliases='e', parents=[cmd_add_or_edit], exit_on_error=False, description="Edit a custom command's message and properties.", help="EDIT HELP")

cmd_edit.add_argument('--unhide', action='store_false', dest='is_hidden')
# cmd_add_or_edit.add_argument('--visible', '-v', action='store_false', dest='is_hidden')
# cmd_edit.add_argument('--rename', '-r', nargs=1)
cmd_edit.add_argument('--enable', action='store_true', dest='is_enabled')

other_cmd_actions = subparsers.add_parser('!cmd', add_help=False)
other_cmd_actions.add_argument('command', nargs='+')

cmd_delete = subparsers.add_parser('delete', parents=[other_cmd_actions], aliases=('remove',), exit_on_error=False, description="Delete commands.", help="Multiple commands may be deleted at once.")
cmd_disable = subparsers.add_parser('disable', parents=[other_cmd_actions], exit_on_error=False, description="Disable commands.", help="Multiple commands may be disabled at once.")
cmd_enable = subparsers.add_parser('enable', parents=[other_cmd_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")
# cmd_ = subparsers.add_parser('enable', parents=[other_cmd_actions], exit_on_error=False, description="Enable commands.", help="Multiple commands may be enabled at once.")

class InvalidArgument(Exception): ...
class InvalidSyntax(Exception): ...


def parse(parser, msg):


# After which indexes can args be parsed?
# * = yes if arg is not a flag

# edit foo -p  vip bar baz
# edit foo -p  vip -c  5
# edit foo -i -p vip
# 0    1   2   3   4   5
# n    n   *   y   n   y

    # edit x
        # if args[1] in valid_flags:
            # return "The first argument must be the command name."
        # last_result = parser.parse_args(args)
        # continue

    args = msg.split()
    if len(args) < 3:
        return f"Syntax Error: Not enough arguments. <!cmd syntax info>"
    num_args = 3
    # last_result: argparse.Namespace = None
    last_result: argparse.Namespace = "Nothing parsed..."
    valid_flags = ('--permissions', '-p', '--aliases', '-a', '--count', '-c', '--hide', '-i', '--disable', '-d',  ) # '--invisible', '-i')
    if args[0] == 'edit':
        valid_flags += ('--rename', '--enable', '--unhide', ) # '--visible', '-v')

    # edit x y ...
    for i, _ in enumerate(args):
        if i < 3:
            continue
        print(i, args[:i])

            # if args[i] in valid_flags:
                # print("args[i] is a flag; continuing")
                # continue
            # num_args += 1
            # i += 1
        # else:
            # offset = 2

        if args[i] in valid_flags:
            print("args[i] is a flag")
            # if args[i+1] in valid_flags:
                # print("Next arg is also a flag...")
            # if args[i-1] in valid_flags:
                # print("Found end of args?")
                # return parser.parse_args(args[:i+2])

        if args[i-1] in valid_flags:
            print("Last arg was a flag")

            # Is the next thing not a valid arg, meaning the beginning of the message?
            if not any(a in valid_flags for a in args[i+1:i+3]):
                print("!!! No flags in next 2 words")
                # print(i, args[:i])
                # num_args += 1
                # i += 2
                # return "Finished parsing"

            # Else
        try:
            # num_args += offset
            last_result = parser.parse_args(args[:i+1])
            # last_result = parser.parse_args(args[:i+offset])
            # print(last_result)
            num_args += 1

        except SystemExit as exc:
            print("SysEx")
            print(last_result)
            # if args[i-2] in valid_flags:
                # print(f"!!! {args[i-2]=}: 2 Args ago was a flag; incrementing num_args")
            #num_args += 1
            #if args[i-2] in valid_flags:
                ## print("SUCCESSFUL")
                #return None, last_result, msg.split(None, num_args)[-1]

        except argparse.ArgumentError:
            print("ArgErr")
            if args[i] not in valid_flags:
                return "Invalid argument?"
                # continue
                return "Missing or invalid arg?"
            #print(last_result)
            print("Current arg is a flag")
            num_args += 1


            #except:
                #print("Exception")
                #print(f"{i=}, {args[i]=}")
                #print(i, args[:i+1])
                #print(f"{num_args=}, {len(args)=}")
                #if not any(a in valid_flags for a in args[i:i+1]):
                    #print("Finished parsing")
                #continue

    #if 2 < num_args != len(args) + 1:
    # if not (num_args == len(args) and args[num_args] in valid_flags):
    print("End of loop")
    print(f"{num_args=}, {len(args)=}")
    if len(args) == num_args:
        return last_result
    return last_result, msg.split(None, num_args)[-1], # [-1]
    # else: return num_args
    # pass


