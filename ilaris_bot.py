#!/usr/bin/env python3
# Imports
import discord
from discord.ext import commands
import logging
import basic_paths
from cogs.generalCog import GeneralCommands
from cogs.groupsCog import GroupCommands

with open(basic_paths.rjoin("token")) as token_file:
    token = token_file.readline()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(
    filename='discord.log',
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
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
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. See `!help` for all commands.")
    if isinstance(error, commands.BadArgument):
        usage = f"{bot.command_prefix}{ctx.command.name}: {ctx.command.help}"
        await ctx.send(f"Failed converting an argument\nCorrect usage: {usage}")
    elif isinstance(error, Exception):
        if ctx.command:
            help = f"{bot.command_prefix}{ctx.command.name}: {ctx.command.help}"
        else:
            help = "Unexpected Error."
        await ctx.send(f"Command Execution failed\n{help}")


@bot.event
async def on_command(ctx):
    server = ctx.guild.name
    user = ctx.author
    command = ctx.command
    logging.info("'{}' used '{}' in '{}'".format(user, command, server))


bot.run(token)  # , log_handler=handler
