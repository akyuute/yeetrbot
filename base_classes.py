from utils import str_to_bool
import twitchio
import sys
import time
import inspect
from typing import Iterable, Dict, Tuple
import dataclasses as dc
from configparser import ConfigParser
from argparse import ArgumentParser


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

        cmd_conf = self['COMMANDS']
        require_message = self['COMMANDS'].get('require_message', "t")
        override_builtins = self['COMMANDS'].get('override_builtins', "t")
        case_sensitive = self['COMMANDS'].get('case_sensitive', "f")

        self.require_message = str_to_bool(require_message)
        self.override_builtins = str_to_bool(override_builtins)
        self.case_sensitive = str_to_bool(case_sensitive)

        self.base_command_name = cmd_conf['base_command_name']
        aliases = (a for a in cmd_conf.items() if '_command_alias' in a[0])
        alias_dict = {k.removesuffix('_command_alias'): v for k, v in aliases}
        self.base_command_aliases = alias_dict


class RegisteredChannel(twitchio.Channel):
    '''Class for base channel objects instantiated
    from the database and modified as needed.'''
    __slots__ = (
        'id',
        'name',
        'join_date',
        '_command_aliases',
        '_keyword_aliases',
        '_custom_variables',
        '_ws',
        )

    def __init__(self, uid: int, name: str, join_date: int = None, bot=None):
        if bot is not None:
            super().__init__(name, bot._connection)
        self.id = uid
        self.name = name
        self.join_date = round(time.time()) if join_date is None else join_date
        # self.join_date = join_date or round(time.time()) or 0
        self._command_aliases = {}
        self._keyword_aliases = {}
        self._custom_variables = {}

    def __repr__(self):
        name = self.name[:8] + "..." if len(self.name) > 16 else self.name
        return f"<{self.__class__.__name__}(name={name}, id={self.id})>"

    async def resolve_command(self, name: str):
        command = self._command_aliases.get(name, None)
        return command

    @property
    def display_name(self) -> str:
        return NotImplemented

    @property
    def custom_commands(self) -> set:
        return set(c for c in self._command_aliases.values()
                   if isinstance(c, CustomCommand))

    @property
    def custom_command_aliases(self) -> dict:
        return {a: c for a, c in self._command_aliases.items()
                if isinstance(c, CustomCommand)}

    @property
    def built_ins(self) -> set:
        return set(c for c in self._command_aliases.values()
                   if isinstance(c, BuiltInCommand))

    @property
    def built_in_aliases(self) -> dict:
        return {a: c for a, c in self._command_aliases.items()
                if isinstance(c, BuiltInCommand)}

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

    def qualifies(self, context: twitchio.ext.commands.Context) -> bool:
        pass


class Rank(UserScope):
    pass


class Context(twitchio.ext.commands.Context):
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

#    __slots__ = (
#        "name",
#        "message",
#        "channel_id",
#        "author_id",
#        "modified_by",
#        "aliases",
#        "perms",
#        "count",
#        "cooldowns",
#        "case_sensitive",
#        "is_hidden",
#        "is_enabled",
#        "ctime",
#        "mtime",
#        "expire",
#        )

#    def __init__(
#        self,
#        **attrs
#        ):

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
        aliases: Iterable[str] = None
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

#    def __init__(self, name: str, func, **attrs):
#        self.name = name
#        self.callback = func
#        self.instance = None
#        self.channel_id = attrs.get('channel_id', None)
#        self.syntax = attrs.get('syntax', None)
#        self.aliases: Iterable[str] = attrs.get('aliases', None)
#        self.perms: str | dict = attrs.get('perms', None)
#        self.count: int = attrs.get('count', None)
#        self.cooldowns: Dict[str|Rank, int] = attrs.get('cooldowns', None)
#        self.case_sensitive = attrs.get('case_sensitive', False)
    
        _: dc.KW_ONLY
        name: str
        callback: Callable[[Context], None]
        channel_id: int # = None
        # instance # = None
        aliases: Iterable[str] = None
        perms: str = None
        count: int = None
        cooldowns: Dict[Rank, int] = None
        case_sensitive: bool = False
        is_hidden: bool = False
        is_enabled: bool = True

    async def __call__(self, context: Context) -> None:
        await self.invoke(context)

    async def invoke(self, context: Context) -> None:
        if callable(self._callback):
            await self._callback(context)
            self._count += 1

