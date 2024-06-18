#!/usr/bin/env python3
import traceback
import logging
import logging.handlers
import discord
from discord.ext import commands
from discord.ext.commands import after_invoke

import config
from config import DATA
from config import messages as msg
from cogs.generalCog import GeneralCommands
from cogs.group import organize_group
from cogs.groupsCog import GroupCommands
from utility.sanitizer import sanitize

import typing

# TODO: not sure where this belongs:
NO_UPDATE_COMMAND_LIST = ["glist"]

cfg = config  # TODO remove me
msg = cfg.messages

handler = logging.handlers.RotatingFileHandler(
    filename=DATA/'discord.log', 
    encoding='utf-8', 
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
log = logging.getLogger('discord')

# NOTE: all mentions are disabled by default (links work but without ping)
bot = commands.Bot(
    command_prefix='!',
    intents=discord.Intents().all(),
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
)


# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(GroupCommands(bot))

@bot.event
async def on_message(ctx):
    try:
        await bot.process_commands(ctx)
    except Exception as e:
        print(e)
        log.error(e)

@bot.event
async def on_command_error(ctx, error):
    if ctx.command.has_error_handler():
        return  # Do not handle commands that have their own handler
    logging.debug(traceback.format_exc())
    if isinstance(error, commands.CommandNotFound):
        response = config.commands.get(ctx.invoked_with, {}).get("reply")
        if response:
            await ctx.send(response)
            return
        else:
            await ctx.send(msg["cmd_not_found"])
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(msg["bad_args"].format(
            pre=ctx.prefix, cmd=ctx.command.name, sig=ctx.command.signature
        ))
    elif isinstance(error, commands.errors.BadArgument):
        await ctx.send(msg["bad_args"].format(
            pre=ctx.prefix, cmd=ctx.command.name, sig=ctx.command.signature
        ))
    elif isinstance(error, Exception):
        if ctx.command:
            info = f"{bot.command_prefix}{ctx.command.name}: {ctx.command.help}"
        else:
            info = msg["unexpected_error"]
        await ctx.send(msg["cmd_failed"].format(info=info))
        raise error


@bot.event
async def on_command_completion(ctx):
    log.info("'{}' used '{}' on '{}' in '{}'".format(
        ctx.author, ctx.message.content, ctx.guild.name, ctx.channel
    ))
    if (ctx.command.cog_name == "GroupCommands" 
        and ctx.command.name not in NO_UPDATE_COMMAND_LIST):
        channel = discord.utils.get(ctx.guild.text_channels,
            name=config.settings.get("groups_channel"))
        if channel:
            await channel.purge()
            for result_str in organize_group.list_groups(sanitize(ctx.guild.name)):
                await channel.send(result_str)
        else:
            log.info("No group channel found.")


@bot.event
async def on_reaction_add(reaction, user):
    log.warning("Reaction added")
    # Check if the reaction is on the bot's message and the emoji is the delete emoji
    if (reaction.message.author == bot.user 
        and reaction.emoji == "❌" 
        and user.guild_permissions.administrator
        and user != bot.user):
        # Delete the message
        await reaction.message.delete()


bot.run(config.settings["token"], log_handler=None)
