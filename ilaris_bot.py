#!/usr/bin/env python3
# Imports
from ast import parse
import logging
import logging.handlers
import traceback

import yaml
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands import after_invoke

import argparse

import config
from config import DATA, ROOT

CONFIG = ROOT / "config"

NO_UPDATE_COMMAND_LIST = ["glist"]


parser = argparse.ArgumentParser(description="Run the Ilaris Discord Bot")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
parser.add_argument("--settings", type=str, help="Path to a settings file", default=CONFIG/"settings.yml")
args = vars(parser.parse_args())

config.load(config, args)

with open(DATA/"token") as token_file:
    token = token_file.readline()


from cogs.generalCog import GeneralCommands
from cogs.group import organize_group
from cogs.groupsCog import GroupCommands
from utility.sanitizer import sanitize_single


handler = logging.handlers.RotatingFileHandler(
    filename=DATA/'discord.log', 
    encoding='utf-8', 
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', 
    handlers=[handler]
)




# Credentials
intents = discord.Intents().all()
# Create bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Function to read CSV and create a dictionary


# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(GroupCommands(bot))


@bot.event
async def on_command_error(ctx, error):
    logging.info(traceback.format_exc())
    if isinstance(error, commands.CommandNotFound):
        response = cfg.commands.get(ctx.invoked_with, {}).get("reply")
        if response:
            await ctx.send(response)
            return
        else:
            await ctx.send(msg["cmd_not_found"])
    elif isinstance(error, commands.errors.MissingRequiredArgument) or \
        isinstance(error, commands.errors.BadArgument):
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
    logging.info("'{}' used '{}' on '{}' in '{}'".format(
        ctx.author, ctx.message.content, ctx.guild.name, ctx.channel
    ))
    if (ctx.command.cog_name == "GroupCommands" 
        and ctx.command.name not in NO_UPDATE_COMMAND_LIST):
        channel = discord.utils.get(ctx.guild.text_channels, name=cfg.settings.get("groups_channel"))
        if channel:
            await channel.purge()
            for result_str in organize_group.list_groups(sanitize_single(ctx.guild)):
                await channel.send(result_str)
        else:
            logging.info("No group channel found.")


@bot.event
async def on_reaction_add(reaction, user):
    # Check if the reaction is on the bot's message and the emoji is the delete emoji
    if (reaction.message.author == bot.user and reaction.emoji == "❌" and user.guild_permissions.administrator
            and user != bot.user):
        # Delete the message
        await reaction.message.delete()


bot.run(token)  # , log_handler=handler
