import argparse

def edit(*args):
    # print(args)
    namespace, message = args[0]
    print(namespace)
    print(' '.join(message))
    print("Function 'edit' ran.")

parser = argparse.ArgumentParser(prog='!commands', description="Manage channel commands from chat.", ) # exit_on_error=False)
subparsers = parser.add_subparsers()

cmd_edit = subparsers.add_parser('edit', aliases='e', description="Edit a custom command's properties.")
cmd_edit.set_defaults(func=edit)
cmd_edit.add_argument('command', nargs='+') # dest='command_name')
cmd_edit.add_argument('--permissions', '-p', choices="everyone rank= moderator vip owner".split(), dest='perms') # required=True)
cmd_edit.add_argument('--aliases', '-a', nargs='+')
cmd_edit.add_argument('--count', '-c', type=int, required=False)
cmd_edit.add_argument('--is_enabled', choices="true t 1 false f 0".split(), required=False)
cmd_edit.add_argument('--enable', '-e', action='store_true', dest='is_enabled')
cmd_edit.add_argument('--disable', '-d', action='store_false', dest='is_enabled')
cmd_edit.add_argument('message', nargs='*', )

# parser_args = "edit foo1 \\-t foo2 -c 4 my   <3-space-gap> message is here." # --permissions moderator"
parser_args = "edit \"foo \\\" \\-p bar\" -p vip -c 3 --o unrec --enable a very long, \" '' \\ \\\\weird message" # --permissions moderator"

# enum = enumerate(list(parser_args))
# enum = enumerate(parser_args.replace('  ', '   ').split(' '))
# pairs = [pair for pair in enum if pair[1] != '']
# print(' '.join(parser_args.casefold().split()))
# print(list(enumerate(parser_args.split())))
# print(pairs)

args = parser.parse_known_args(parser_args.split(' '))
# args = parser.parse_args(parser_args.split())
# print(len(parser_args))
# print(f"Original msg:\n{parser_args}\nCommand message after parsing:\n{' '.join(args[-1]):>49}")
# args[0].func(dict(zip(['args', 'message'], args)))
args[0].func(args)
# print(args)
