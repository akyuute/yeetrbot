"""
!command subcmd msg...
parse(msg) -> dict
mapping[subcmd] = func
func(dict) -> 

register_command(dict)
"""

import re
import shlex

def update_command():
    pass

def delete_command():
    pass

def list_commands():
    pass

def show_command():
    pass

def describe_command():
    pass


def parse_commands_str(action: str, msg: str):
    '''Parses the message passed to !commands or an alias and calls the
    corresponding function responsible for updating the datebase or relating
    information.'''

    variables = ('aliases', 'perms', 'count', 'is_enabled', 'desc')
    # variables = ('is_raw', 'aliases', 'perms', 'count', 'is_enabled', 'desc')
    # flags = ('-r', '-a', '-p', '-c', '-t', '-d')
    flags = ('-a', '-p', '-c', '-t', '-d')
    fields = dict.fromkeys(variables, None)
    arg_switch = {k: v for k, v in zip(flags, variables)}
    # if msg.startswith("-r "):
        # print(re.findall(r'(\"|\')(.*?)(\1)', "-r 'my longer command name' -a alias"))
        # args = re.findall(r'(\"|\')(.*?)(\1)', "-r 'my longer command name' -a alias")
        # re.findall(r'(\"|\')(.*?)(\1)', "-r 'my longer command name' -a alias")[1]


    # args = msg.split()
    # print(args)

    # msg = msg.replace(r"\\", r"\\\\")
    # msg = re.sub('(\')', r"\\\\\\\1", msg)

    msg = msg.replace(r"'", r"\'")
    # msg = msg.replace(r'"', r'\"')
    # msg = msg.replace(r"\\", r"\\\\")

    print(msg)
    print(f'{msg!r}')
    print(f"{msg.lstrip()[0:3] = }")
    if msg.lstrip()[0:3] == '-r ':
        lexer = shlex.shlex(msg, posix=True, punctuation_chars=True)
        # lexer.escapedquotes = "'"
        # lexer.escapedquotes = "\""
        # lexer.wordchars += "'"
        # lexer.wordchars += "\\"
        args = list(lexer)
        # del args[0]
        fields['is_raw'] = True
        fields['command_name'] = args[1].replace("\\\'", "'")
        # fields['command_name'] = args[1].replace(r"\\\\", "")
    else:
        fields['is_raw'] = False
        args = msg.split()
    # print(*args)
    print(args)

    
    for i, arg in enumerate(args):
        if i < len(args) - 1:
            if arg in flags:
                fields[arg_switch[arg]] = args[i + 1]

            if fields['is_raw'] == None:
                fields['command_name'] = args[0] # .replace(r"\\\'", r"'")
            # else:

                # pass

    # fields['command_name'] = args[0].replace("\\'", r"'")
    print(fields['command_name'])
    print(*[field for field in fields.values()])
    # fields['command_name'] = ' '.join(args[:2])
    fields['message'] = msg.split(maxsplit=len([v for v in fields.values() if v != None]) * 2 + 1)[-1].replace("\\", "")
    fields['channel_id'] = None
    print(fields)

    if action == 'add':
        fields['is_enabled'] = 1
    if action == 'disable':
        fields['is_enabled'] = 0 
    elif action == 'enable':
        fields['is_enabled'] = 1 

    subcmds = ('add', 'edit', 'disable', 'enable', 'delete', 'show', 'describe', 'list')

    cmd_mappings = (
        *[update_command] * 4
        , delete_command
        , show_command
        , describe_command
        , list_commands
    )
    cmd_switch = {k: v for k, v in zip(subcmds, cmd_mappings)}

    # print(cmd_switch[action])
    # print(fields)
    # print(fields['command_name'])
    # print(fields['desc'])
    # print(fields['message'])



'''
!command <add|edit|delete|disable|enable|show|list> -r[aw]=1 <name> -a=aliases -p=perms -c=count -t=toggle -d=description(must have quotes) <message>
!addcmd -r[aw]=1 <name> -a=aliases -p=perms -c=count -t=toggle -d=description(must have quotes) <message>
!editcmd -r[aw]=1 <name> -a=aliasses -p=perms -c=count -t=toggle -n=new_name -d=description(must have quotes) <message>
!delcmd <name>
!disable <name>
!enable <name>
!showcmd <name> (displays the command's name, description and message)
!listcmd <count>
'''
    # return (is_raw , name , aliases , perms , count , is_builtin , is_enabled , desc , message)


if __name__ == '__main__':
    cmd = 'add'
    # msg = "mycomm -a   a's -p moderator   -d  's  -t enabled aweifj iaefj aeifjanfiaf"
    # msg = "\"mycomm thing\'\" -a another_name -p moderator -d \"My description\""
    # print(msg)


    # msg = '"mycomm\' thing" -a another_name -p moderator -d "My description" my message is right\'s here.'
    # msg = '  -r "mycomm  \' \'thing" -a another_name -p moderator -d "My description" my message is right\'s here.'
    msg = input('> ')

    parse_commands_str(cmd, msg)
    # print(f"{parse_commands_str('add', msg) = }")

# -r "mycomm \\ ' '\"thing" -a another_name -p moderator -d "My description" my message is right's quote here.
# -r "mycomm \\ ' '\"thing" -a another_name -p moderator -d "My description" my message is right's here.