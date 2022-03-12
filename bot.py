#bot.py

from twitchio.ext import commands
# from twitchio import channel, chatter, FollowEvent, ChannelInfo, Clip, User
import random
import re
import os
import sqlite3
from db._create_tables import _create_tables
import csv
import atexit
# from os import environ
from dotenv import load_dotenv
from my_commands import string_commands
# from my_commands.string_commands import derp, uwu, uhm
#from alpha.eng_funcs import EngFuncs as eng
#eng = EngFuncs()

# Load and assign environment variables
env_file = ".bot.env"
load_dotenv(env_file)
env_keys = ('ACCESS_TOKEN', 'CLIENT_ID', 'BOT_NICK', 'BOT_PREFIX', 'INITIAL_CHANNELS')
ENV: dict = {k: v for k, v in os.environ.items() if k in env_keys}
ENV['BOT_PREFIX'] = ENV['BOT_PREFIX'].split(',')
ENV['INITIAL_CHANNELS'] = ENV['INITIAL_CHANNELS'].split(',')


channel_data_fields = ['channel', 'commands', 'death_count']
channel_data_file = 'db/channel_data.csv'


class RegistrationError(Exception): ...
class CustomError(Exception): ...


class Yeetrbot:
    '''Contains methods for database exchanges and additional functionality.'''
    channel_data: dict
    # def __init__(self):
    #     self._init_database()
    #     self.channel_data = self._fetch_channel_data()
    #     self._fetch_commands()
    #     self._fetch_builtins()

    def _init_database(self):
        self.db_conn = sqlite3.connect("db/botdb.db")
        self.db = self.db_conn.cursor()
        with self.db_conn:
            for stmt in _create_tables:
                self.db.execute(stmt)

    def _fetch_channel_data(self):
        '''Retrieves registered channels from the database.'''
        keys = ('id', 'name', 'display_name', 'history')
        records = self.db.execute("select * from channel")
        channel_data = {}
        for rec in records:
            chan_id = int(rec[0])
            channel_data[chan_id] = {k: v for k, v in zip(keys, rec)} # , 'commands': {}, 'variables': {}}
            channel_data[chan_id]['commands'] = {}
            channel_data[chan_id]['variables'] = {}
        # print("Join:", self.db.execute("select * from channel join command on channel.id = command.chan_id").fetchall())
        return channel_data

    def _fetch_commands(self):
        '''Retrieves the registered custom commands for each channel
        and stores them in the channel_data dict.'''
        keys = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_enabled')
        # records = self.db.execute("select * from command where is_builtin = 0")
        records = self.db.execute(f"select {','.join(keys)} from command where is_builtin = 0")
        # custom_commands = {int(rec[2]): {k: v for k, v in zip(keys, rec)} for rec in records}
        custom_commands = [{k: v for k, v in zip(keys, rec)} for rec in records]
        # print(custom_commands)
        # for channel in self.channel_data:
        # try:
            # 'commands' in self.channel_data.values()
        # except KeyError:
            # self.channel_data[channel_user_id]['commands'] = {}
            # print("Unable to fetch commands")
            # pass
        # finally:
            # self.channel_data[channel_user_id]['commands'][command_name] = new_dict
        try:
            for com in custom_commands:
                self.channel_data[com['chan_id']]['commands'][com['name']] = com
        except KeyError as exc:
            print("_fetch_commands: KeyError")
            print(exc.args[0])

    def _fetch_built_ins(self):
        '''Retrieves the registered built-in commands for each channel
        and stores them in the channel_data dict.'''
        keys = ('chan_id', 'name', 'aliases', 'perms', 'count', 'is_enabled')
        records = self.db.execute(f"select {','.join(keys)} from command where is_builtin = 1")
        # builtins = {int(rec[1]): {k: v for k, v in zip(keys, rec)} for rec in records}
        built_ins = [{k: v for k, v in zip(keys, rec)} for rec in records]
        try:
            for com in built_ins:
                self.channel_data[com['chan_id']]['built_ins'][com['name']] = com
        except KeyError:
            print("_fetch_global_commands: KeyError")

    @property
    def channels(self):
        data = self.channel_data
        names = [data[chan]['name'] for chan in data]
        names += ENV['INITIAL_CHANNELS']
        return set(names)




    def register_channel(self, channel_user_id: int, name: str, display_name: str):
        '''Registers a new channel for the bot to serve. If the channel is
        registered, its values are updated.'''
        keys = ('id', 'name', 'display_name', 'history')
        new_dict = {k: v for k, v in zip(keys, [channel_user_id, name, display_name])}
        # self.channel_data[channel_user_id].update(new_dict)
        self.channel_data[channel_user_id] = new_dict
        _sql = "insert into channel(id, name, display_name) values (?,?,?)"
        # if channel_user_id not in self.channel_data:
        try:
            with self.db_conn:
                self.db.execute(_sql, [str(channel_user_id), name, display_name])
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])
            return exc

    def register_command(self, channel_user_id: int, command_name: str, message: str, aliases: str = None, perms: str = 'everyone', count: int = None):
        if not channel_user_id in self.channel_data:
            return RegistrationError("This channel is not registered.")
        keys = ('chan_id', 'name', 'aliases', 'message', 'perms', 'count', 'is_builtin', 'is_enabled')
        new_dict = {k: v for k, v in zip(keys, [channel_user_id, command_name, aliases, message, perms, count, 0, 1])}
        try:
            isinstance(self.channel_data[channel_user_id]['commands'], dict)
        except KeyError:
            self.channel_data[channel_user_id]['commands'] = {}
        finally:
            self.channel_data[channel_user_id]['commands'][command_name] = new_dict

        _sql = "insert into command(chan_id, name, aliases, message, perms, count, is_builtin, is_enabled) values (?,?,?,?,?,?,?,?)"
        # print([str([*new_dict.values()])])
        # if command_name not in self.channel_data[channel_user_id]['commands']:
        try:
            with self.db_conn:
                # self.db.execute(_sql, [str(channel_user_id), command_name, message, ])
                # self.db.execute(_sql, [str(v) for v in new_dict.values() if v not None])
                self.db.execute(_sql,[v for v in new_dict.values()])
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])
                # return exc

    def register_built_in(self, channel_user_id: int, command_name: str, aliases: str = None, perms: str = 'everyone', count: int = None):
        if not channel_user_id in self.channel_data:
            return RegistrationError("This channel is not registered.")
        keys = ('chan_id', 'name', 'aliases', 'perms', 'count', 'is_enabled')
        new_dict = {k: v for k, v in zip(keys, [channel_user_id, command_name, aliases, perms, count, 1])}
        try:
            isinstance(self.channel_data[channel_user_id]['commands'], dict)
        except KeyError:
            self.channel_data[channel_user_id]['commands'] = {}
        finally:
            self.channel_data[channel_user_id]['commands'][command_name] = new_dict

        _sql = "insert into command(chan_id, name, aliases, message, perms, count, is_builtin, is_enabled) values (?,?,?,?,?,?,?,?)"
        # print([str([*new_dict.values()])])
        # if command_name not in self.channel_data[channel_user_id]['commands']:
        try:
            with self.db_conn:
                # self.db.execute(_sql, [str(channel_user_id), command_name, message, ])
                # self.db.execute(_sql, [str(v) for v in new_dict.values() if v not None])
                self.db.execute(_sql,[v for v in new_dict.values()])
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])
                # return exc
        # pass

    def register_variable(self, varname: str):
        _sql = "insert into variable(var_name) values (?)"
        try:
            with self.db_conn:
                self.db.execute(_sql)
                self.db_conn.commit()
        except sqlite3.Error as exc:
            print(exc.args[0])

    def set_chan_variable(self, varname, value):
        _sql = "update ..."
        pass


class ChatBot(commands.Bot, Yeetrbot):
    '''Base class for bot configs containing default commands and variables.'''
    def __init__(self):
        self._init_database()
        self.channel_data = self._fetch_channel_data()
        self._fetch_commands()
        self._fetch_built_ins()
        # print(self.channels)
        # self.register_channel(1234, 'foo', 'Foo')
        # self.register_channel(4567, 'bar', 'Bar')
        # self.register_command(1234, 'testcomm', "My new command.",)
        # self.register_command(4567, 'testcomm2', "My newer command.",)
        self.display_name = ENV['BOT_NICK']
        print(self.channel_data)
        # print(self.channels)
        # print(self.com)



        # Yeetrbot.__init__(self)
        # commands.Bot.__init__(self,
        super().__init__(
            token=ENV['ACCESS_TOKEN'],
            client_secret=ENV['CLIENT_ID'],
            nick=ENV['BOT_NICK'],
            prefix=ENV['BOT_PREFIX'],
            # prefix='!',
            # initial_channels=ENV['INITIAL_CHANNELS'] # + self.channels
            initial_channels=self.channels
            )
        # self.channels = ENV['INITIAL_CHANNELS']


    # @property
    # def channels(self):
    #     data = self.channel_data
    #     names = []
    #     try:
    #         for chan in data:
    #             names.append(next(data[chan]['name']))
    #     finally:
    #         return names


    async def global_before_invoke(self, ctx: commands.Context):
        chan = await ctx.channel.user()
        # chan.id
        # cmd = str(ctx.message.content).partition(' ')[0]
        cmd = ctx.command
        # if cmd.name not in self.channel_data[chan.id]['commands']:
            # ctx.is_valid = False if cmd.name == '!join' else True
            # pass
        print(cmd.name, chan.id, chan.display_name)
        # if cmd.name not in self
        # if not cmd in 

        # return await 
        # pass

    async def event_ready(self):
        # Post a message in the console upon connection
        print(f"{self.display_name} is online!")
        # Also post a message in chat upon connection
        for channel in self.connected_channels:
            # await self.get_channel(channel).send(f"{self.display_name} is online!")
            pass

    # async def event(self, name: str = "imdad"):
        # return super().event(name)

    # add this and other event handlers to a cog:
    async def event_message(self, message):
        msg: str = message.content
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Do imdad()
        if str(message.content)[:6].lower().startswith(("i'm ", "i am ", "im ")):
            if random.random() < 0.2:
                await message.channel.send(string_commands.imdad(msg))


        # Print the contents of our message to console...
        # Also may be useful to append to a log file
        #####if message.echo:
        #print(message.content)

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)


    @commands.command(name="testmsg")
    async def command_testmsg(self, ctx: commands.Context):
        msg = ctx.message.content
        au = ctx.author
        # print(au._fetch_channel().user())
        # await ctx.send(str(len(au.user().fetch_followers()) )) # fetch_following())
        # myuserobj = au.user()
        # mychatterobj = ctx.get_user(au.name)
        # print(mychatterobj)
        # print(chatter.Chatter.)

        # print(User("https://twitch.tv/"+str(mychatterobj.channel), {}))

        # print(myuserobj)
        
        # print(chatter.User.fetch_followers(()))
        # print(chatter.User.fetch_followers(au.user()))
        # await ctx.send(str(au.user()))
        # print(au.id, au.mention, au.name, au.display_name, au.color)
        # print(ctx.command.  parse_args(ctx, None, parsed={}))
        # await ctx.send("")
        #fetch_followers())
        # print(isinstance(msg, str))
        #await ctx.send(str(ctx.author.color))#{ctx.message.content}))
        # msg = "!testmsg arg1 arg2 arg3"
        # print(msg)))
        # print(msg.lstrip(r"^.*\s"), msg.removeprefix(r"!.*\s"))
        # print(ctx.message.raw_data)
        # channel_usr = await ctx.channel.user()
        # my_usr = await ctx.author.user()
        # bot_usr = ctx.get_user('yeetrbot')

        # print(bot_usr)
        # print(channel_usr.id)
        # print(my_usr.id)
        # print(self.regd_channels)
        # await ctx.send("I'm awake!")
    

    @commands.command(name="join")
    async def join_new_channel(self, ctx: commands.Context):
        '''Attempts to register a new channel to the database when invoked within the bot's own channel.'''
        msg = str(ctx.message.content).partition(" ")[2]
        if msg:
            await ctx.send(f"{ctx.author.mention}, the !join command must be blank.")
            return
        uid = ctx.author.id
        username = ctx.author.name
        display_name = ctx.author.display_name
        if uid not in self.channel_data:
            try:
                self.register_channel(uid, username, display_name)
                await self.join_channels([username])
                await ctx.send(f"{ctx.author.mention}, I have successfully joined your channel. See you there!")
                # self.db.execute("commit")
                # print("ran !join")
                print(self.channel_data)
            except Exception as exc:
                print(exc.args[0])
                await ctx.send(f"""{ctx.author.mention}, I encountered an
                    error while registering your channel. Please contact
                    @derek_YEETr, who will help resolve the situation.""")
        else:
            await ctx.send(f"{ctx.author.mention}, I am already in your channel!")




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
    #         # await self.get_channel(channel).send(f"{self.display_name} is online!")
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
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # super().__init__()
        # pass

    @commands.command(name="!uwu")
    async def command_uwu(self, ctx: commands.Context):
        # msg = ctx.message.content.lstrip(f"{BOT_PREFIX}{uwu.__name__}")
        msg = str(ctx.message.content).partition(' ')[2]
        # print(msg)
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

    @commands.command(name="derp", ) # aliases=("testmsg",))
    async def command_derp(self, ctx: commands.Context):
        # msg = ctx.message.content
        msg = str(ctx.message.content).partition(' ')[2]
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



    #@commands.command()
    #async def hello(self, ctx: commands.Context):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        #await ctx.send(f'Hello, {ctx.author.display_name}!')
    



    ###############async def add_command(self, command=commands.Command(name, func)):

    ###############add_command(self, command=commands.Command(name='!pleasework', func=print("did this work?")))
    #Bot.add_command(self, command)


def prepare_bot(bot: commands.Bot, cogs: tuple[commands.Cog]):
    '''Prepare a bot object with cogs, etc.'''
    for cog in cogs:
        bot.add_cog(cog)





mybot = ChatBot()

# print(bot.commands)
# print(tuple(mybot.get_db_channels()))
# print(mybot.get_db_channels)
# mybot.query_db("INSERT into channel(user_id, name, display_name) values (12345, 'my_user2', 'My_User2')")
# mybot.register_channel(123456, "my_user3", "My_User3")
print("Registered channels:", mybot.channels)



# @atexit.register
# def preserve_data():
#     with open(channel_data_file, 'w') as f:
#         writer = csv.DictWriter(f, fieldnames=channel_data_fields)
#         writer.writerows(channel_data)

prepare_bot(bot=mybot, cogs=(StrCommands(mybot), EventsCog(mybot), MiscCommandsCog(mybot)))
# mybot.remove_command("join")
mybot.db_conn.commit()
mybot.run()




# bot.run() is blocking and will stop execution of any below code here until stopped or closed.

'''
@bot.event
async def event_ready():
    'Called once when the bot goes online.'
    print(f"{os.environ['BOT_NICK']} is online!")
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(os.environ['CHANNEL'], f"/me is online!")

@bot.event
async def event_message(ctx):
    'Runs every time a message is sent in chat.'

    # make sure the bot ignores itself and the streamer:
    if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
        return

 

    
    await bot.handle_commands(ctx)


    if 'hello' in ctx.content.lower():
        await ctx.channel.send(f"Hi, @{ctx.author.name}!")


@bot.command(name='test')
async def test(ctx):
    await ctx.send('/me is online!')

@bot.command(name='randword')
async def rand_word(ctx):
    msg = eng.rand_word()
    await ctx.send(msg)

@bot.command(name='randdef')
async def rand_def(ctx):
    msg = eng.rand_def()
    await ctx.send(msg)

@bot.command(name='define')
async def define(ctx):
    query = str(ctx.content).replace('!define','')
    # offer_choice = f"[num_matches] definitions found for '[word]'. Please choose a definition (1-[num_matches] / ALL):\n> " 
    msg = eng.define(query)
    if eng.needs_input:
        await ctx.send(eng.offer_choice)
        # choice =  await ctx.next_input or something()

    # print(str(ctx.content).replace('!define',''))
    await ctx.send(msg)

korok_list = []

@bot.command(name='klist')
async def klist(ctx):
    global korok_list 
    def get_missing(my_list):
        if korok_list == []:
            msg = "No Koroks reported missing."
        else: return f"Missing Koroks: {', '.join(my_list)}"
    #query = str(ctx.content).replace(',','').replace('!klist','').split(' ').remove('')
    query = [word.replace(',','') for word in str(ctx.content).split() if word != '!klist']
    if len(query) > 0:
        if query[0] == 'remove':
            korok_list.remove(query[1])
            msg = f"Removed 1 Korok. {get_missing(korok_list)}"
        elif query[0] == 'clear':
            korok_list.clear()
            msg = "Korok list cleared :D"
        elif len(query) >= 1:
            korok_list.extend(query)
            msg = get_missing(korok_list)
    else: msg = get_missing(korok_list)
    #msg = query

    await ctx.send(msg)


if __name__ == "__main__":
  bot.run()

'''