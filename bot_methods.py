async def event_ready(self):
    '''Have the bot do things upon connection to the Twitch server.'''
    print(f"{self.display_name} is online!")
    # Post a message in each registered channel's chat upon connection:
    # for channel in self.connected_channels:
    # notify = f"{self.display_name} is online!"
    #     await self.get_channel(channel).send(msg)
    #     pass

# Maybe add this and other event handlers to a cog in bot.py:
async def event_message(self, message):
    # Messages sent by the bot have `echo` = True.
    # Ignore bot messages:
    if message.echo:
        return

    msg: str = message.content
    # msg: str = re.split(r'PRIVMSG\s\#\w+\s:', message.raw_data, 1)[1]
    # Do imdad():
    if msg[:6].lower().startswith(("i'm ", "i am ", "im ")):
        if random.random() < 0.2:
            await message.channel.send(string_commands.imdad(msg))
    # Channel triggers and keywords can eventually be handled here as well.

    await self.handle_commands(message)

async def global_before_invoke(self, ctx: Context):
    '''Sets some useful values as Context attributes.'''
    # TwitchIO splits and re-joins message content internally.
    # To preserve message whitespace, regex the raw data from Twitch:
    raw = re.split(r'PRIVMSG\s\#\w+\s:', ctx.message.raw_data, 1)[1]
    ctx.cmd, _, ctx.msg = raw.partition(' ')
    ctx.author_id = int(ctx.author.id)
    channel = await ctx.channel.user()
    ctx.chan_as_user = channel
    # ctx.channel_copy = self._registry.get(channel.id)
    print("--> ", channel.display_name, ctx.cmd, ctx.msg)


