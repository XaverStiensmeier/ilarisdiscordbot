#!/usr/bin/env python3
import os

import discord
from discord.ext import commands

from config import RESOURCES
from config import messages as msg
from cogs.general import differ
from cogs.general import ilaris_database
from cogs.general import parse_die

cards = [os.path.splitext(filename)[0] for filename in os.listdir(RESOURCES/"manoeverkarten")]
NAMED_ROLLS = [
    ("IIIoo", "2@5d20"), ("IIIo", "2@4d20"), ("Ioo", "1@3d20"), 
    ("Io", "1@2d20"), ("ooIII", "4@5d20"), ("oIII", "3@4d20"), 
    ("ooI", "3@3d20"), ("oI", "2@2d20"), ("III", "2@3d20"), ("I", "1d20")
]


class GeneralCommands(commands.Cog):
    """
    Commands for handling general stuff
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=msg["helloilaris_help"])
    async def helloilaris(self, ctx):
        await ctx.reply(msg["helloilaris_reply"].format(author=ctx.author.id))

    @commands.command(help=msg["creatures_help"], aliases=["kreatur", "kreaturen", "creature"])
    async def creatures(self, ctx, creature: str = commands.parameter(default=None, description=msg["creatures_desc"])):
        params = f"suche={creature}" if creature else ""
        await ctx.reply(msg["creatures_url"].format(params=params))

    @commands.command(help=msg["ilaris_help"])
    async def ilaris(self, ctx, arg: str = commands.parameter(description=msg["ilaris_desc"])):
        if arg.isnumeric() and int(arg):
            if 219 >= int(arg) > 0:
                await ctx.reply(
                    file=discord.File(RESOURCES/"ilaris"/f"ilaris-{arg.zfill(3)}.png"))
            else:
                await ctx.reply(msg["page_limit"])
        else:
            await ctx.reply(ilaris_database.get_database_entry(name=arg))

    @commands.command(help=msg["card_help"], aliases=['karte'])
    async def card(self, ctx, arg: str = commands.parameter(description=msg["card_desc"])):
        name, three_best = differ.closest_match(arg, cards)
        if name:
            file_path = cfg.RESOURCES/"manoeverkarten"
            file_path_jpg = os.path.join(file_path, f"{name}.jpg")
            file_path_png = os.path.join(file_path, f"{name}.png")
            if os.path.isfile(file_path_jpg):
                file_path = file_path_jpg
            elif os.path.isfile(file_path_png):
                file_path = file_path_png
            else:
                await ctx.reply(msg["card_wrong_type"])
            await ctx.reply(file=discord.File(file_path))
            if three_best:
                await ctx.reply(msg["card_best_matches"].format(best=three_best))
        else:
            await ctx.reply(msg["card_not_found"])

    @commands.command(help=msg["r_help"], aliases=['w'])
    async def r(self, ctx, roll: str = commands.parameter(default="III", description=msg["r_desc"]),
                identifier: str = commands.parameter(default="", description="Identifier.")):
        roll = roll.replace(" ", "")
        for key, value in NAMED_ROLLS:
            roll = roll.replace(key, value)
        total_result_str, total_result = parse_die.parse_roll(roll)
        total_result = msg["r_result"].format(
            author=ctx.author.display_name,
            identifier=identifier,
            result=total_result,
            details=total_result_str
        )
        await ctx.message.delete()
        response = await ctx.send(total_result)
        # await response.delete(delay=300)
        await response.add_reaction("❌")

    # TODO: allow sending files only for specific user ids
    # @commands.command(help="Admin only: Gets debug information", hidden=True)
    # @commands.has_permissions(administrator=True)
    # async def what(self, ctx):
    #     await ctx.author.send(file=discord.File(bp.djoin("discord.log")))
    #     await ctx.author.send(file=discord.File(bp.djoin("groups.yml")))
