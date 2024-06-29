#!/usr/bin/env python3
import os

import discord
from discord.ext import commands
from discord import app_commands

from config import RESOURCES
from config import messages as msg
from cogs.general import differ
from cogs.general import ilaris_database
from cogs.general import parse_die
from ui.views import HpButtons

cards = [os.path.splitext(filename)[0] for filename in os.listdir(RESOURCES/"manoeverkarten")]
NAMED_ROLLS = [  # TODO: should this be part of settings?
    ("IIIoo", "2@5d20"), ("IIIo", "2@4d20"), ("Ioo", "1@3d20"), 
    ("Io", "1@2d20"), ("ooIII", "4@5d20"), ("oIII", "3@4d20"), 
    ("ooI", "3@3d20"), ("oI", "2@2d20"), ("III", "2@3d20"), ("I", "1d20")
] # TODO: should we make them case insensitive?


def emojify_number(num):
    s = str(num)
    emos = ["0️⃣", "1️⃣", " 2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    return "".join([emos[int(i)] for i in s])


class GeneralCommands(commands.Cog):
    """Commands for handling general stuff
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
            file_path = RESOURCES/"manoeverkarten"
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
    
    @app_commands.command(name="hp", description="Health Points")
    async def hp(self, inter, name: str="Healthbar"):
        buttons = HpButtons(name)
        embed = buttons.embed()
        await inter.response.send_message(embed=embed, view=buttons, ephemeral=False)

    
    @commands.command(help=msg["r_help"], aliases=['w'])
    async def r(self, ctx, 
            roll: str = commands.parameter(default="III", description=msg["r_desc"]),
            identifier: str = commands.parameter(default="", description="Identifier."),
            difficulty: int = commands.parameter(default=None, description="Difficulty.")
        ):
        original = ctx.message.content
        roll = roll.replace(" ", "")
        for key, value in NAMED_ROLLS:
            roll = roll.replace(key, value)
        content, total_result, img = parse_die.parse_roll(roll)
        # total_result_text = msg["r_result"].format(
        #     author=ctx.author.display_name,
        #     identifier=identifier,
        #     result=total_result,
        #     details=total_result_str
        # )
        await ctx.message.delete()
        # allow passing only difficulty (as first arg)
        if not difficulty:
            try:
                difficulty = int(identifier)
                identifier = ""
            except ValueError:
                pass
        title = identifier if identifier else "Erfolgswert"
        # emo_num = emojify_number(total_result)
        title = f"🎲 {identifier if identifier else msg['r_title']} {total_result}"
        # TODO: remove this.. we only want colors for given difficulty
        # ew1, ew2 = 12, 16  # should this be part of settings (ew1, ew2)?
        # if difficulty is not None:
        #     ew1, ew2 = difficulty, difficulty
        # if total_result >= ew2:
        #     color = discord.Color.green()
        # elif total_result >= ew1:  # never happens for given difficulty
        #     color = discord.Color.gold()
        # else:
        #     color = discord.Color.red()
        # content = f"{ctx.author.display_name}: {total_result_str}"
        color = None
        if difficulty is not None:
            if total_result < difficulty:
                color = discord.Color.red()
                content += f"\n\n🚫 {msg['r_fail']}"
            else:
                color = discord.Color.green()
                content += f"\n\n✅ {msg['r_success']}"
            content += f" ({msg['r_difficulty']}: {difficulty})"
        embed = discord.Embed(title=title, description=content, color=color)
        img_url = f"https://ilaris-online.de/static/bilder/d20s/default.png"
        if img is not None:
            # pick d20 img
            img_url = f"https://ilaris-online.de/static/bilder/d20s/{img}.png"
        embed.set_thumbnail(url=img_url)
        response = await ctx.send(f"<@{ctx.author.id}>: {ctx.message.content}", embed=embed)
        # await response.delete(delay=300)
        await response.add_reaction("❌")
