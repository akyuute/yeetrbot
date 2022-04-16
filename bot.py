#bot.py

from twitchio.ext import commands
import random
import re
import os

from errors import (
    ChannelNotFoundError,
    CommandNotFoundError,
    RegistrationError,
    NameConflict,
    ParsingError,
    DatabaseError,
    )

from parse_config import Config
from base_classes import Yeetrbot
from my_commands import string_commands
# from my_commands.string_commands import derp, uwu, uhm


class ChatBot(commands.Bot, Yeetrbot):
    '''Base class for bot configs containing default commands and variables.'''
    def __init__(self, config: Config | dict):
        self._db_file = config['DATABASE'].get('db_file', 'db/bot.db')
        self._init_database(self._db_file)
        self._init_channels()
        self._init_commands()

        self.display_name = config['CREDENTIALS']['bot_nick']
        initial_channels = config['CREDENTIALS']['initial_channels'].split()
        self._initial_channels = set(initial_channels + self.registered_channels)

        cmd_conf = config['COMMANDS']
        self.prefixes = cmd_conf.get('command_prefixes', "!").split()
        self._base_command_name = cmd_conf['base_command_name']
        self._default_perms = cmd_conf.get('default_perms', "everyone")
        self._default_count = int(cmd_conf.get('default_count', 0))
        self._require_message = config.require_message
        self._override_builtins = config.override_builtins

        aliases = (a for a in cmd_conf.items() if '_command_alias' in a[0])
        alias_dict = {k.removesuffix('_command_alias'): v for k, v in aliases}
        self._base_command_aliases = alias_dict

        super().__init__(
            token=config['CREDENTIALS']['access_token'],
            client_secret=config['CREDENTIALS']['client_id'],
            nick=self.display_name,
            prefix=self.prefixes,
            initial_channels=self._initial_channels
            )

        self.global_before_invoke = self._global_before_invoke
        self.event_message = self._event_message
        self.event_ready = self._event_ready


    @commands.command(name="join")
    async def command_join(self, ctx: commands.Context):
        if ctx.chan_as_user.id != self.user_id:
            return
        try:
            resp = self._join_channel(ctx)
        except RegistrationError as exc:
            resp = exc.args[0]
        await self.join_channels([ctx.author.name])
        await ctx.send(f"{ctx.author.mention}: {resp}")

    @commands.command(name='cmd', aliases=('addcmd', 'editcmd', 'delcmd', 'disable', 'enable'))
    #self._base_command_aliases
    async def command_cmd(self, ctx: commands.Context):
        resp = ""
        if not ctx.author.is_mod:
            await ctx.send(f"{ctx.author.mention}: Only moderators or higher can use this command.")
            return
        # cmd_perms = channel.commands[cmd].perms
        # if channel.users[auth_id].rank not in cmd_perms:
            # await ctx.send(f"{ctx.author.mention}: ")
        try:
            resp = self._manage_custom_command(ctx)

        except ChannelNotFoundError as exc:
            resp = exc.args[0]
            print("Lookup error:")
            # Do nothing: This channel is not registered
            return
        except (
            RegistrationError,
            NameConflict,
            CommandNotFoundError,
            ParsingError,
            DatabaseError,
            NotImplementedError
        ) as exc:
            resp = exc.args[0]
            print(repr(exc).replace("(", ": ", 1)[:-1])
        print("Response:", resp)
        await ctx.send(f"{ctx.author.mention}: {resp}")

    @commands.command(name="testmsg")
    async def command_testmsg(self, ctx: commands.Context):
        # mychatterobj = ctx.get_user(au.name)
        # print(User("https://twitch.tv/"+str(mychatterobj.channel), {}))
        # print(chatter.User.fetch_followers(()))
        # print(ctx.message.raw_data)
        # print(self._registry)
        await ctx.send("I'm awake!")
    
        pass



class EventsCog(commands.Cog):
    '''A default class for bot events.
    Useful for annonymous commands, triggers, timers, etc.'''
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # async def event_ready(self):
    #     # Post a message in the console upon connection
    #     # print(f'{self.nick} is online!')
    #     print(f"{self.bot.display_name} is online!")
    #     # Also post a message in chat upon connection
    #     for channel in self.bot.channels:
    #         # await self.registered_channel(channel).send(f"{self.display_name} is online!")
    #         pass

    # commands.Cog.event()
    # async def event_message(self, message):
    #     '''Try to match each message sent with a prefix-less command,
    #     keyword, or other trigger in several dictionaries that point to
    #     commands.'''
    #     if message.echo:
    #         return
    #     print(message.content)
    #     # self.event()

    #     await self.bot.handle_commands(message)
        # pass
        


class StrCommands(commands.Cog):
    '''Cog class for string commands.
    Run prepare_bot() to add this cog to a bot.'''
    def __init__(self, bot):
        self.bot = bot
        pass

    @commands.command(name="!uwu")
    async def command_uwu(self, ctx: commands.Context):
        msg = ctx.msg
        resp = string_commands.uwu(msg)
        # error_occurred = len(resp) == 2
        if len(resp) == 2:
            error_occurred = resp[1] != 0
            if error_occurred:
                error_mention = f"{ctx.author.mention}: "
                resp = error_mention + resp[0]
            else: resp = resp[0]
        await ctx.send(resp)

        # await ctx.send(uwu(msg))
        # return uwu(query)

    @commands.command(name="derp")
    async def command_derp(self, ctx: commands.Context):
        msg = ctx.msg
        resp = string_commands.derp(msg)
        if len(resp) == 2:
            error_occurred = resp[1] != 0
            if error_occurred:
                error_mention = f"{ctx.author.mention}: "
                resp = error_mention + resp[0]
            else: resp = resp[0]
        await ctx.send(resp)

        

class MiscCommandsCog(commands.Cog):
    '''
    '''
    def __init__(self, bot: commands.Bot) -> None:
        try:
            with open('db/death_counts.csv', 'r') as f:
                death_counts = {k: int(v) for k, v in csv.reader(f)}
                # print("Death counts:", death_counts)
            # with open(channel_data_file, 'r') as f:
            #     death_counts = {item['channel']: int(item['death_count']) for item in channel_data}
                # print(death_counts)
        except FileNotFoundError as exc:
            # print("Uh oh... Using empty dict")
            death_counts = {}

        self.bot = bot
        self.death_counts = death_counts

    @commands.command(name="!deaths")
    async def command_death_counter_adn(self, ctx: commands.Context):
        '''Displays channel death count and lets mods update it.'''
        msg = str(ctx.message.content).partition(' ')[2]
        try:
            try:
                deaths = self.death_counts[ctx.channel.name]
            except KeyError:
                self.death_counts[ctx.channel.name] = 0
                deaths = self.death_counts[ctx.channel.name]

            resp = None
            reassigned = False
            command_syntax = '''Syntax: "!deaths [+|-|++|--]"
                                or "!deaths [+|-|set] <integer>"'''

            if not msg:
                if deaths != 1:
                    resp = f"There have been {deaths} deaths."
                else:
                    resp = "There has been 1 death."

            elif ctx.author.is_mod:
                args = msg.split()[:2]
                # print(args)

                if len(args) == 1:
                    one_arg = {
                        '+': lambda x: x + 1,
                        '-': lambda x: x - 1,
                        '++': lambda x: x + 1,
                        '--': lambda x: x - 1,
                    }
                    try:
                            new_count = one_arg[args[0]](
                                self.death_counts[ctx.channel.name])
                            deaths = new_count
                            reassigned = True
                    except KeyError:
                        try:
                            deaths = int(args[0])
                            reassigned = True
                        except ValueError:
                            resp = f'''
                                {ctx.author.mention}: Invalid argument: 
                                "{args[0]}". ''' + command_syntax

                elif len(args) == 2:
                    two_args = {
                        '+': lambda x, y: x + y,
                        '-': lambda x, y: x - y,
                        'set': lambda x, y: y,
                        '' : lambda x, y: y
                    }
                    try:
                        new_count = two_args[args[0]](
                            self.death_counts[ctx.channel.name], int(args[1]))
                        deaths = new_count
                        reassigned = True
                    except (KeyError, ValueError):
                        try:
                            deaths = int(args[1])
                            reassigned = True
                        except ValueError:
                            # arg1_is_int = int(args[0])
                            # print(arg1_is_int)
                            resp = f'''
                                {ctx.author.mention}: Invalid argument: 
                                "{args[1] if args[0] in two_args.keys()
                                    else
                                    args[0]}". ''' + command_syntax
                                    # or arg1_is_int else

                else:
                    resp = f"{ctx.author.mention}: Invalid syntax. " + command_syntax

            if deaths <= 0:
                deaths = 0
            self.death_counts[ctx.channel.name] = deaths

            if reassigned:
                resp = f"Death count set to {deaths}."
            if resp:
                await ctx.send(resp)
            else:
                return

            # with open(channel_data_file, 'a') as f:
                # writer = csv.DictWriter(f, channel_data_fields)
                # writer.writerow()
            with open('db/death_counts.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow([ctx.channel.name, deaths])

        except Exception as exc:
            print(exc)
            await ctx.send(exc.args[0])

        '''
            # 0 args:
        !deaths                             -> return the count
            # 1 arg:
        !deaths <int>                       -> count = <int>
        !deaths +/-                         -> count ++ / count --
        !deaths clear                       -> count = None
            # 2 args:
        !deaths set <int>                   -> count = <int>
        !deaths +/- <int>                   -> count +/-= <int>
        '''

def prepare_bot(bot: commands.Bot, cogs: tuple[commands.Cog]):
    '''Prepare a bot object with cogs, etc.'''
    for cog in cogs:
        bot.add_cog(cog)


if __name__ == '__main__':
    bot_config = Config(file="bot.conf")
    mybot = ChatBot(bot_config)

    # print(bot.commands)
    # print(tuple(mybot.get_db_channels()))
    # print(mybot.get_db_channels)
    # mybot.register_channel(123456, "my_user3", "My_User3")
    # print("Registered channels:", mybot.registered_channels)
    print("Joined channels:", mybot._initial_channels)

    prepare_bot(bot=mybot, cogs=(StrCommands(mybot), EventsCog(mybot), MiscCommandsCog(mybot)))
    mybot._db_conn.commit()
    mybot.run()

