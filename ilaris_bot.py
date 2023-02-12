#!/usr/bin/env python3
# Imports
import discord
from discord.ext import commands
import logging
import logging.handlers
import basic_paths
from cogs.generalCog import GeneralCommands
from cogs.groupsCog import GroupCommands
from cogs.group import organize_group
import traceback

NO_UPDATE_COMMAND_LIST = ["glist"]

with open(basic_paths.rjoin("token")) as token_file:
    token = token_file.readline()

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
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
        await ctx.send(f"Command not found. See `!help` for all commands.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f"Correct Usage: {ctx.prefix}{ctx.command.name} {ctx.command.signature}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Correct Usage: {ctx.prefix}{ctx.command.name} {ctx.command.signature}")
    elif isinstance(error, Exception):
        if ctx.command:
            info = f"{bot.command_prefix}{ctx.command.name}: {ctx.command.help}"
        else:
            info = "Unexpected Error."
        await ctx.send(f"Command Execution failed: {info}")
    raise error


@bot.event
async def on_command(ctx):
    logging.info("'{}' used '{}' on '{}' in '{}'".format(ctx.author, ctx.command, ctx.guild.name, ctx.channel))
    if ctx.command.cog_name == "GroupCommands" and ctx.command.name not in NO_UPDATE_COMMAND_LIST:
        channel = discord.utils.get(ctx.guild.text_channels, name="open-groups-list")
        if channel:
            await channel.purge()
            for result_str in organize_group.list_groups():
                await channel.send(result_str)
        else:
            logging.info("No group channel found.")

bot.run(token)  # , log_handler=handler
