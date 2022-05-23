#bot.py

# from twitchio.ext import commands
import random
import re
import os

from errors import (
    ChannelNotFoundError,
    CommandNotFoundError,
    RegistrationError,
    NameConflict,
    InvalidSyntax,
    ParsingError,
    DatabaseError,
    )

from base_classes import Config, Context
from bot import Yeetrbot
import commands 
# import built_in_commands


class ChatBot(Yeetrbot):
    '''Class for the bot in which new built-in commands can be defined.'''
    # @commands.built_in
    async def command_join(self, ctx: Context):
        pass
    pass


if __name__ == '__main__':
    mybot = ChatBot(config='config.yml')

    # print("Joined channels:", mybot._initial_channels)

    # mybot._db_conn.commit()
    #mybot.run()

    import asyncio
    # import parse_commands
    import parse_commands_new
