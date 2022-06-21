import asyncio
import re
import json
from urllib.parse import urljoin
import requests

import discord
from discord.ext import commands
from base_classes import Config


API_URL = "https://api.twitch.tv/helix/"
CONFIG = Config('config.yml')
# PREFIX = ('!', '')
PREFIX = '!'

class TwitchAPI:
    def __init__(self, client_id: str, token: str, secret: str = None):
        if secret is not None:
            pass
        self.headers = {
            "Authorization": f"Bearer {token}", 
            "Client-Id": client_id
        }

    async def fetch_user_data(self, name: str = None, id: int|str = None):
        login_query = "" if name is None else f"login={name}" 
        id_query = "" if id is None else f"id={id}" 
        path_and_parameters = f"users?{login_query}&{id_query}"
        url = urljoin(API_URL, path_and_parameters)
        data = requests.get(url, headers=self.headers)
        return data.json()
        

# class DiscordCommands:
    # def 

# class MyClient(discord.Client):
class MyBot(commands.Bot):
    async def on_ready(self):
        print(f"Logged in as {self.user!r}")

    async def on_message(self, message):
        print(f"Got message from {message.author!r}: {message.content!r}")
        await self.process_commands(message)
##        recognized_greetings = ('hello', 'hi', 'howdy', 'shalom'
##        )
##        if any(g in message.content.lower() for g in recognized_greetings):
##            if (
##                self.user.name.lower() in message.content.lower()
##                or self.user in message.mentions
##            ):
##                await message.channel.send(f"Hi there, {message.author.mention}!")


    async def run_with_cleanup(self):
        async with self:
            self.run(CONFIG.bot['credentials']['discord_token'])


intents = discord.Intents.default()
# intents.
# intents.message_content = True

# client = MyClient(intents=intents)
# client.run(CONGIG.bot['discord_token'])
mybot = MyBot(command_prefix=PREFIX, intents=intents)

@mybot.command(name='embed')
async def command_embed(ctx, ): # *args):
    '''Sends an embed parsed from user input.'''
    print(f"Running command_embed()")
    argstr = ctx.message.content.removeprefix(ctx.prefix + ctx.invoked_with)
    # fields = list(eval(' '.join(args)))
    # fields = list(eval(argstr))
    # print(f"{fields=}")
    to_emb = eval(argstr)
    print(f"{to_emb = }")
    fields = to_emb.pop('fields')
    emb = discord.Embed.from_dict(to_emb)
    # emb = discord.Embed(title='Test embed')
    # emb.fields = fields  # These need to be EmbedProxy objects!
    for f in fields:
        emb.add_field(**f)
    await ctx.channel.send(embed=emb)

api = TwitchAPI(
    client_id=CONFIG.bot['twitch_api_credentials']['client_id'],
    token=CONFIG.bot['twitch_api_credentials']['token'])

@mybot.command(name='twitchdata')
async def command_twitchdata(ctx, ):
    # print(f"Running command_twitchdata()")
    argstr = ctx.message.content.removeprefix(ctx.prefix + ctx.invoked_with).strip()
    # print(f"{argstr = }")
    args = re.split(r'[=:]|\s+', argstr)

    if not args[0]:
        error = "!twitchdata syntax: '!twitchdata [name=]<name> | id=<id>'"
        await ctx.channel.send(error)
        return
    elif len(args) == 1:
        params = {'name': args[0]}
    else:
        params = dict(zip(args[::2], args[1::2]))
    print(f"{params = }")

    data = await api.fetch_user_data(**params)
    # await ctx.channel.send("Command ran")
    await ctx.channel.send(json.dumps(data))





# asyncio.run(mybot.run_with_cleanup())

mybot.run(CONFIG.bot['discord_credentials']['token'])

