import sys
from argparse import ArgumentParser
from configparser import ConfigParser

def str_to_bool(value: str):
    '''Returns `True` or `False` bools for truthy or falsy strings.'''
    truthy = "true t yes y on 1".split()
    falsy = "false f no n off 0".split()
    pattern = value.lower()
    if pattern not in truthy + falsy:
        raise ValueError(f"Invalid argument: {pattern!r}")
    match = pattern in truthy or not pattern in falsy
    return match


class Config(ConfigParser):
    '''Class for objects with data from config files.'''
    def __init__(self, file):
        cli_parser = ArgumentParser()
        cli_parser.add_argument('--config')

        super().__init__(empty_lines_in_values=False)
        config_file = cli_parser.parse_args(sys.argv[1:]).config or file
        with open(config_file, 'r') as f:
            self.read_file(f)
        self.file = file
        require_message = self['COMMANDS'].get('require_message', "t")
        override_builtins = self['COMMANDS'].get('override_builtins', "t")
        self.require_message = str_to_bool(require_message)
        self.override_builtins = str_to_bool(override_builtins)

