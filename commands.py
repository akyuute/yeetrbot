from base_classes import Context, Rank, CustomCommand, BuiltInCommand
from utils import get_rand_index
import command_funcs
from errors import *
# from commands import register_built_in
# from core_commands import built_in

from typing import Iterable, Dict
import re
import random
import string
import dataclasses as dc
import time


# Setting this constant to your own allows you to save time when changing
# command names and prefixes without refactoring every one in this file.
# If you need one command to use a different prefix, change or remove the
# 'prefix' parameter from its 'register_built_in()' decorator.
# If you don't like my names and prefer to rename each command individually,
# set this constant to an empty string "" and you can be on your way!
PREFIX = "!"


def register_built_in(
    *,
    name: str = None,
    aliases: Iterable[str] = [],
    perms: str = None,
    cooldowns: dict = None,
    case_sensitive=False,
    prefix: str = "",
    syntax: str | Dict[str, str] = None,
    cls=BuiltInCommand
    ) -> BuiltInCommand:
    '''A decorator that registers a new built-in command, adding its name
    and aliases to the `built_in_commands` dict.'''

    def decorator(func):
        name_ = prefix + (name or func.__name__)
        aliases_ = set(prefix + a for a in aliases) if aliases else aliases
        cmd = cls(
            name=name_,
            callback=func,
            global_aliases=aliases_,
            perms=perms,
            case_sensitive=case_sensitive,
            cooldowns=cooldowns,
            syntax=syntax,
            )
        return cmd
    return decorator

class CoreCommands:
    '''Functions and syntax for core built-in commands.
    It is best not to alter these.
    Instead, their names and aliases are to be set in the config file.
    They do not use the `register_built_in()` decorator.'''
    # syntaxes = {}
    SYNTAXES = {
        'add': {
            "": "Imagine this is the '!cmd add' syntax message.",
            '--help': """Imagine this is the '!cmd add' help message."""
        }, 
        'edit': {
            "": "Imagine this is the '!cmd edit' syntax message.",
            '--help': """Imagine this is the '!cmd edit' help message."""
        }
    }

    async def cmd_manage_commands(ctx: Context):
        resp = ""
        if not ctx.author.is_mod:
            await ctx.send(f"{ctx.author.mention}: Only moderators or higher can use this command.")
            return
        # cmd_perms = channel.commands[cmd].perms
        # if channel.users[auth_id].rank not in cmd_perms:
            # await ctx.send(f"{ctx.author.mention}: ")
        try:
            # resp = bot._manage_custom_command(ctx)
            resp = ctx.bot.cmd_manager.manage_commands(ctx)

        except ChannelNotFoundError as exc:
            resp = exc.args[0]
            print("Lookup error:")
            # Do nothing: This channel is not registered
            return
        except (
            RegistrationError,
            NameConflict,
            CommandNotFoundError,
            InvalidSyntax,
            CommandHelpMessage,
            ParsingError,
            DatabaseError,
            NotImplementedError
        ) as exc:
            resp = exc.args[0]
            print(str(exc.__class__))
        print("Response:", resp)
        await ctx.send(f"{ctx.author.mention}: {resp}")

    # @register_built_in(name=P+'join')
    async def cmd_join(ctx: Context):
        '''Registers a new channel to the database when invoked within
        the bot's Twitch channel and sends a response.'''
        if ctx.channel.id != bot.user_id:
            return

        username = ctx.author.name
        error_preface = f"Failed registering channel {username!r}"
        resp = ""

        if ctx.author_id not in ctx.bot._channels:
            try:
                ctx.bot.register_channel(ctx.author_id, username)
                resp = "I've successfully joined your channel. See you there!"
                print(f"Registered new channel {username}")
            except RegistrationError as exc:
                resp = f"{error_preface}. Registration error: {exc.args[0]}"
            except DatabaseError as exc:
                resp = f"{error_preface}. Database error: {exc.args[0]}"
        else:
            resp = "I am already in your channel!"
        await bot.join_channels(tuple(ctx.author.name))
        await ctx.send(f"{ctx.author.mention}: {resp}")

    
    async def cmd_usernamechanged(ctx: Context):
        user_id = ctx.author.id
        if user_id != ctx.channel.id:
            return
        resp = ""
        name = ctx.author.name
        try:
            ctx.bot.refresh_user_data(user_id, name)
        except DatabaseError as exc:
            resp = f"Failed to update username {name}"



@register_built_in(name="uwu", prefix=PREFIX)
async def cmd_uwu(ctx: Context):
    resp = await command_funcs.uwu(ctx.msg_body)
    await ctx.send(resp)

@register_built_in(name="derp", prefix=PREFIX)
async def cmd_derp(ctx: Context):
    resp = await command_funcs.derp(ctx.msg_body)
    await ctx.send(resp)

@register_built_in(name="uhm", prefix=PREFIX)
async def cmd_uhm(ctx: Context):
    resp = await command_funcs.uhm(ctx.msg_body)
    await ctx.send(resp)

@register_built_in(name="ye", prefix=PREFIX)
async def cmd_ye(ctx: Context):
    resp = await command_funcs.ye(ctx.msg_body)
    await ctx.send(resp)

@register_built_in(name="i'm", aliases=["i am", "im",])
async def cmd_imdad(ctx: Context):
    resp = await command_funcs.im_dad(ctx.msg_body)
    await ctx.send(resp)

@register_built_in(name="shuffle", prefix=PREFIX)
async def cmd_shuffle_words(ctx: Context):
    resp = await command_funcs.shuffle_words(ctx.msg_body)
    await ctx.send(resp)

