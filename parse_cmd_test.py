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

def parse_cmd_add_edit(parser, msg):
    if len(msg.split()) < 3:
        return InvalidSyntax(f"ctx.author.mention(): Syntax error: Command missing message or arguments.")
    else:
        args = msg.split()
        num_args = 2
    last_result: argparse.Namespace = None
    flags = ('--permissions', '-p', '--aliases', '-a', '--count', '-c', '--enable', '--disable')
    if args[0] == 'edit':
        flags += ('--rename',)

    # edit foo -p vip bar baz
    # edit foo bar baz blah
    for i, _ in enumerate(args):
        print(i, args[i])
        # This means 
        if len(msg.split()) < 3:
            return InvalidSyntax(f"ctx.author.mention(): Syntax error: Command missing message or arguments.")

        if i < 3:
            if args[i] in flags:
                return InvalidArgument(f"ctx.author.mention(): Name error: {args[i]!r} is not a valid command name.")
            continue

        if args[i] in flags:
            if i == len(args) - 1:
                return "Last arg is a flag."

            # if i % 2 != 0:
            # if args[i-1] in flags:
                # print("odd")
                print("Here")
                please_parse = args[:i+2]
            else:
                print("No, here")
                print(args[:i+1])
                # return None, last_result, msg.split(None, num_args)[-1]
                continue
        else:
            print("Here, actually")
            please_parse = args[:i+1]

        try:
            last_result = parser.parse_args(please_parse)
            num_args += 1
            print("made it")
            print(last_result)
            print(args[:i+1])
        except argparse.ArgumentError as exc:
            print("ArgumentErr")
            print(last_result)
            print(args[:i+1])
            return InvalidSyntax(f"ctx.user.mention(): Syntax error: {exc}")
        except SystemExit as exc:
            print("SysEx")
            print(last_result)
            if args[i-2] in flags:
                # print("SUCCESSFUL")
                return None, last_result, msg.split(None, num_args)[-1]
            else:
                print("Unrecognized arg")
                return None, last_result, msg.split(None, num_args)[-1]
                return InvalidArgument(f"ctx.user.mention(): Unrecognized argument: {args[i-1]!r}")

    print("SUCCESS")
    print(f"{num_args = }")
    return last_result, msg.split(None, num_args)[-1]
    # pass


