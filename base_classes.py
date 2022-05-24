from utils import str_to_bool
# import parse_commands
import twitchio
from twitchio.ext.commands import Context as TwitchIOContext
import sys
import time
import inspect
import itertools
from collections import OrderedDict
from typing import Iterable, Dict, Tuple, Callable
import dataclasses as dc
from configparser import ConfigParser
from argparse import ArgumentParser
from pathlib import Path
import strictyaml as yaml


class Config:
    def __init__(self, file: Path = None):
        cli_parser = ArgumentParser()
        cli_parser.add_argument('--config')
        config_file = cli_parser.parse_args(sys.argv[1:]).config or file

        with open(config_file, 'r') as f:
            raw_data = f.read()
        self.__dict__ = yaml.load(raw_data).data
        self.file = config_file
        self.bot['heartbeat'] = float(self.bot.get('heartbeat', 30))

        cmds = self.commands
        dfts = cmds['defaults']

        channels_set_min_perms = cmds.get('channels_set_min_perms', "t")
        channels_set_case = cmds.get('channels_set_case', "f")
        require_message = cmds.get('require_message', "t")

        cmds['channels_set_min_perms'] = str_to_bool(channels_set_min_perms)
        cmds['chnls_set_case'] = str_to_bool(channels_set_case)
        cmds['require_message'] = str_to_bool(require_message)
        dfts['perms'] = dfts.get('default_perms', "everyone")
        dfts['count'] = int(dfts.get('default_count', 0))
        dfts['case_sensitive'] = str_to_bool(dfts.get('case_sensitive', "f"))

        default_cd = dfts.get('cooldowns', None)
        if default_cd is None:
            ranks = "everyone vip moderator owner".split()
            default_cd = dict.fromkeys(ranks, 1.0)
        dfts['cooldowns'] = {rk: float(cd) for rk, cd in default_cd.items()}

        # Use setdefault() here??
        # dfts['perms'] = default_perms
        # dfts['count'] = int(default_count)
        # dfts['case_sensitive'] = str_to_bool(default_case_sensitive)
        #cmds['core_built_ins']['manage_commands']['func_switch'] = {
        #    'add': parse_commands.add_command,
        #    'edit': parse_commands.edit_command,
        #    'delete': parse_commands.delete_command,
        #    'disable': parse_commands.toggle_command,
        #    'enable': parse_commands.toggle_command,
        #    #'alias': parse_command.edit_command
        #}

        # override_builtins = self.commands.get('override_builtins', "t")
        # self.commands['override_builtins'] = str_to_bool(override_builtins)


class RegisteredChannel(twitchio.Channel):
    '''Class for base channel objects instantiated
    from the database and modified as needed.'''
    __slots__ = (
        'id',
        'name',
        'join_date',
        'case_sensitive_commands',
        '_command_aliases',
        '_keyword_aliases',
        # '_alias_lookup',
        '_custom_variables',
        'bot',
        '_ws',
        )

    def __init__(self, uid: int, name: str, join_date: int = None, bot=None):
        if bot is not None:
            super().__init__(name, bot._connection)
            self.bot = bot
        self.id = int(uid)
        self.name = name
        self.join_date = round(time.time()) if join_date is None else join_date
        # self.join_date = join_date or round(time.time()) or 0
        # self.case_sensitive_commands = None
        self._command_aliases = {}
        self._keyword_aliases = {}
        self._custom_variables = {}

    def __repr__(self):
        name = self.name[:8] + "..." if len(self.name) > 16 else self.name
        return f"<{self.__class__.__name__}({name=}, id={self.id})>"

    # async def resolve_command(self, name: str):
        # command = self._command_aliases.get(name, None)
        # return command

    @property
    def _alias_lookup(self):
        # return tuple(self.custom_command_aliases.items())
        # return OrderedDict(self.custom_command_aliases)
        cmds = self.custom_command_aliases.items()
        bins = self.built_in_aliases.items()
        default = self.bot._built_in_command_aliases.items() or ((None, None))
        # print("built-ins at lookup:", default)
        lookup = itertools.chain(cmds, bins, default)
        return lookup

    @property
    def all_the_aliases(self):
        # cmds = OrderedDict(
        #cmds = dict(
        cmds = (
                (a.lower(), c) for a, c in self._command_aliases.items()
                if isinstance(c, CustomCommand)
        )
        if self.bot is None:
            # return OrderedDict(cmds)
            return dict(cmds)
        bins = (
                (a.lower(), c) for a, c in self.bot._built_in_command_aliases.items()
                if isinstance(c, BuiltInCommand)
        )
        print("cmds:", tuple(cmds))
        print("bins:", tuple(bins))
        print(tuple(itertools.chain(cmds, bins)))
        return itertools.chain(cmds, bins)

        # cmds.update(self.bot._built_in_command_aliases.items())
        # return OrderedDict(itertools.chain(
            # self._command_aliases.items(),
            # self.bot._built_in_command_aliases.items()
            # ))

    @property
    def display_name(self) -> str:
        return NotImplemented

    @property
    def custom_command_aliases(self) -> dict:
        return {a.lower(): c for a, c in self._command_aliases.items()
                if isinstance(c, CustomCommand)
                # and c.is_enabled
                }

    @property
    def built_in_aliases(self) -> dict:
        return {a.lower(): c for a, c in self._command_aliases.items()
                if isinstance(c, BuiltInCommand)
                # and c.is_enabled
                }

    @property
    def custom_commands(self) -> set:
        return set(c for c in self._command_aliases.values()
                   if isinstance(c, CustomCommand))

    @property
    def built_ins(self) -> set:
        return set(c for c in self._command_aliases.values()
                   if isinstance(c, BuiltInCommand))

    @property
    def variables(self):
        return self._custom_variables.values()


class UserScope:
    '''Base class for custom and pre-defined ranks,
    e.g. `Everyone`, `Moderator`, etc.'''
    def __init__(self, name, parent = None):
        self._name = name
        self._parent = parent
        self._check = None

    def qualifies(self, context) -> bool:
        pass


class Rank(UserScope):
    pass


class Context(TwitchIOContext):
    def __init__(self, bot, message: twitchio.Message):
        self.bot = bot
        channel_id = int(message.tags['room-id'])
        message._channel = self.bot._channels.get(channel_id)
        message.content = self._restore_whitespace(message._raw_data)
        is_valid = self.check_valid()
        super().__init__(bot=bot, message=message, valid=is_valid)
        # self._scoped = False
        self.invoked_with: str = None
        
    def _restore_whitespace(self, raw_data: str):
        groups = raw_data.split(" ")
        content = " ".join(groups[4:]).lstrip(":")
        return content
    
    # def _restore_whitespace(self):
        # groups = self.message._raw_data.split(" ")
        # self.message.content = " ".join(groups[4:]).lstrip(":")
    
    async def check_valid(self):
        return

    def get_user_scope(self) -> UserScope:
        #self.author.id ... self.bot._channels[self.channel_id].ranks
        #self.author.is_mod
        pass


@dc.dataclass(slots=True)
class CustomCommand:
    _: dc.KW_ONLY
    name: str
    message: str
    channel_id: int
    author_id: int
    name: str
    message: str
    channel_id: int
    author_id: int
    modified_by: int = None
    aliases: Iterable[str] = dc.field(default_factory=list)
    perms: str = None
    count: int = None
    cooldowns: Dict[Rank, int] = dc.field(default_factory=dict)
    case_sensitive: bool = False
    is_hidden: bool = False
    is_enabled: bool = True
    # Times in seconds since epoch; use time.gmtime() to convert to UTC
    ctime: int = round(time.time())
    mtime: int = round(time.time())
    expire: Tuple[int, str] = None

    async def __call__(self, context: Context) -> None:
        await self.invoke(context)

    async def invoke(self, context: Context) -> None:
        await context.send(self.message)
        self.count += 1
        self.last



@dc.dataclass(slots=True)
class BuiltInCommand:

    # Maybe consider using conventional __init__ and __slots__.
    # Don't set the values that default to None,
    # using setdefault() at instantiation by load_channel_builtin()!

#    __slots__ = (
#        'name', 'callback', 'channel_id', 'bot', 'aliases', 'global_aliases', 'perms', 'count', 'cooldowns', 'case_sensitive', 'syntax'
#    )

    _: dc.KW_ONLY
    name: str
    callback: Callable[[Context], None]
    channel_id: int = None
    bot = None # = None  # Necessary?
    aliases: Iterable[str] = dc.field(default_factory=list)
    global_aliases: Iterable[str] = ()
    perms: str = None
    count: int = None
    cooldowns: Dict[Rank, int] = None
    case_sensitive: bool = False
    syntax: str = None
    is_hidden: bool = False
    is_enabled: bool = True

    async def __call__(self, context: Context) -> None:
        # print(f"command {self.name} is running!")
        await self.invoke(context)

    async def invoke(self, context: Context) -> None:
        try:
            await self.callback(context)
        finally: pass
##        except Exception as e:
##            print(f"Failed to process command {context.command!r} "
##                  f"of message {context.message.content!r} "
##                  f"in channel {context.channel.name}: "
##                  f"{e.args[0]}")
##        print(f"{self.name}.count = {self.count}")
        # self.count += 1
        # if callable(self._callback):
            # await self._callback(context)

    @property
    def lc_aliases(self):
        return {a.lower() for a in self._aliases}



