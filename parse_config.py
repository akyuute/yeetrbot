import utils
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
import json
from pathlib import Path


class Config:
    def __init__(self, file: Path = None):
        cli_parser = ArgumentParser()
        cli_parser.add_argument('--config')
        config_file = cli_parser.parse_args(sys.argv[1:]).config or file

        with open(config_file, 'r') as f:
            raw_data = f.read()
            # raw_data = json.loads(f.read())
        # self.obj = utils.comb(raw_data, lambda v: any(p in v for p in "/#;"))
        self.__dict__ = utils.remove_from_keys(
            json.loads(raw_data), lambda k: k.startswith(tuple("/#")))
        self.file = config_file
        self.raw_data = raw_data

#class Config(ConfigParser):
#    '''Class for objects with data from config files.'''
#    def __init__(self, file):
#        cli_parser = ArgumentParser()
#        cli_parser.add_argument('--config')
#
#        super().__init__(empty_lines_in_values=False)
#        config_file = cli_parser.parse_args(sys.argv[1:]).config or file
#        with open(config_file, 'r') as f:
#            self.read_file(f)
#        self.file = file
#
#        cmd_conf = self['COMMANDS']
#        require_message = self['COMMANDS'].get('require_message', "t")
#        override_builtins = self['COMMANDS'].get('override_builtins', "t")
#        self.require_message = str_to_bool(require_message)
#        self.override_builtins = str_to_bool(override_builtins)
#
#        self.base_command_name = cmd_conf['base_command_name']
#        aliases = (a for a in cmd_conf.items() if '_command_alias' in a[0])
#        alias_dict = {k.removesuffix('_command_alias'): v for k, v in aliases}
#        self.base_command_aliases = alias_dict

