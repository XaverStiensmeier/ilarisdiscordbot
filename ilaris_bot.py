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

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# Credentials
TOKEN = "MTA0OTA2NDIyNzIxMTU5NTg0Ng.GKcv_l._nns08bwpEFKgNX20BK4pQZil4dS3lcOih5yW8"
intents = discord.Intents().all()
# Create bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))
    print("Test")
    print("Type", type(GeneralCommands))
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(GroupCommands(bot))
    

bot.run(TOKEN, log_handler=handler)
