#!/usr/bin/env python3
# Imports
import discord
from discord.ext import commands
import logging
import yaml
import signal
import sys
from cogs.generalCog import GeneralCommands
from cogs.groupsCog import GroupCommands

with open("token") as token_file:
    token = token_file.readline()
print(token)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
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
    

bot.run(token, log_handler=handler)
