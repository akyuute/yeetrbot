'''Reads the bot's config file, or generates a
new one if it does not already exist.'''

import os
from configparser import ConfigParser
file = "bot_config.ini"
config = ConfigParser(empty_lines_in_values=False)
bot_config = config.read(file)



def interpret_bool(value: str):
    truthy = "true t yes y on 1".split()
    falsy = "false f no n off 0".split()
    pattern = value.lower()
    if pattern not in truthy + falsy:
        raise ValueError(f"Invalid argument: {pattern!r}")
    match = pattern in truthy or not pattern in falsy
    return match

