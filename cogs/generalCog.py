#!/usr/bin/env python3
import discord
from discord.ext import commands

from cogs.general import ilaris_database
from cogs.general import parse_die


class GeneralCommands(commands.Cog):
    """
    Commands for handling general stuff
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def helloilaris(self, ctx):
        await ctx.send('Hello User!')

    @commands.command(help="Posts an image of the given page if argument is numeric. Else the database entry.")
    async def ilaris(self, ctx, arg: str = commands.parameter(
        description="Number or database entry (for example 4 or 'Duplicatus')")):
        if arg.isnumeric() and int(arg):
            if int(arg) <= 219 and int(arg) > 0:
                await ctx.send(file=discord.File(f"ilaris/ilaris-{arg.zfill(3)}.png"))
            else:
                await ctx.send("Ilaris only has 219 pages.")
        else:
            await ctx.send(ilaris_database.get_database_entry(name=arg))

    @commands.command(help="Rolls a die")
    async def r(self, ctx, roll: str = commands.parameter(default="2@3d20", description="Dice string to parse.")):
        named_rolls = {"I": "1d20", "III": "3d20", "I+": "1@2d20", "I++": "1@3d20", "III+": "2@4d20", "III++": "2@5d20",
                       "+": "2@4d20", "++": "2@5d20"}
        if roll in named_rolls:
            roll = named_rolls[roll]
            await ctx.send(f"Rolling {roll}")
        await ctx.send(parse_die.parseDie(roll))
