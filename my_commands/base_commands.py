

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
        channel_usr = await ctx.channel.user()
        my_usr = await ctx.author.user()
        print(channel_usr.id)
        print(my_usr.id)
        # await ctx.send("I'm awake!")
    
    @commands.command(name="uwu")
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
                print("Death counts:", death_counts)
            # with open(channel_data_file, 'r') as f:
            #     death_counts = {item['channel']: int(item['death_count']) for item in channel_data}
                # print(death_counts)
        except FileNotFoundError as exc:
            # print("Uh oh... Using empty dict")
            death_counts = {}

        self.bot = bot
        self.death_counts = death_counts

    @commands.command(name="deaths")
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
