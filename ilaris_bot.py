#!/usr/bin/env python3
# Imports
import csv
import logging
import logging.handlers
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import after_invoke

from messages import msg
import config as cfg
from cogs.generalCog import GeneralCommands
from cogs.group import organize_group
from cogs.groupsCog import GroupCommands
from utility.sanitizer import sanitize_single


NO_UPDATE_COMMAND_LIST = ["glist"]

with open(cfg.DATA/"token") as token_file:
    token = token_file.readline()

handler = logging.handlers.RotatingFileHandler(
    filename=cfg.DATA/'discord.log', 
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


def load_commands(filename):
    loaded_commands = {}
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            loaded_commands[row['Command']] = row['Response']
    return loaded_commands


# Load commands from CSV
commands_dict = load_commands(cfg.RESOURCES/'text_commands.csv')
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
        response = commands_dict.get(ctx.invoked_with)
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
    if ctx.command.cog_name == "GroupCommands" and \
        ctx.command.name not in NO_UPDATE_COMMAND_LIST:
        channel = discord.utils.get(ctx.guild.text_channels, name="spielrunden")
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
