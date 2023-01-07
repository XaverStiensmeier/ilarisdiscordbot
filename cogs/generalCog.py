#!/usr/bin/env python3
import os

import discord
from discord.ext import commands

import basic_paths
from cogs.general import differ
from cogs.general import ilaris_database
from cogs.general import parse_die

cards = [os.path.splitext(filename)[0] for filename in os.listdir(basic_paths.rjoin("manoeverkarten"))]


class GeneralCommands(commands.Cog):
    """
    Commands for handling general stuff
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Greets the Ilaris Bot.")
    async def helloilaris(self, ctx):
        await ctx.send('Hello User!')

    @commands.command(help="Posts an image of the given page if argument is numeric. Else the database entry.")
    async def ilaris(self, ctx, arg: str = commands.parameter(
        description="Number or database entry (for example 4 or 'Duplicatus')")):
        if arg.isnumeric() and int(arg):
            if 219 >= int(arg) > 0:
                await ctx.send(file=discord.File(basic_paths.rjoin(f"ilaris/ilaris-{arg.zfill(3)}.png")))
            else:
                await ctx.send("Ilaris only has 219 pages.")
        else:
            await ctx.send(ilaris_database.get_database_entry(name=arg))

    @commands.command(help="Posts an image of a specified rule card.", aliases=['karte'])
    async def card(self, ctx, arg: str = commands.parameter(
        description="Name of rule card")):
        name, three_best = differ.closest_match(arg, cards)
        if name:
            await ctx.send(file=discord.File(basic_paths.rjoin(f"manoeverkarten/{name}.png")))
            if three_best:
                await ctx.send(f"Die drei besten Matches sind: {three_best}")
        else:
            await ctx.send("No such rule card...")

    @commands.command(help="Rolls dice.", aliases=['w'])
    async def r(self, ctx,
                roll: str = commands.parameter(default="III",
                                               description="Dice string to parse. e.g. 2d6+3: Sum the result of 2 "
                                                           "6-sided dice and 3. 2@3d20: Roll 3d20 and take the second "
                                                           "highest i.e. (20,15,5) => 15.\n"
                                                           "Special rolls: I: 1d20, III: 2@3d20. Use 'I+' or 'III+' "
                                                           "to indicate fate point usage. "
                                                           "Use '++' with 'I++' or 'III++' to indicate fate point "
                                                           "usage with an aspect.")):
        named_rolls = {"I": "1d20", "III": "2@3d20", "I+": "1@2d20", "I++": "1@3d20", "III+": "2@4d20",
                       "III++": "2@5d20",
                       "+": "2@4d20", "++": "2@5d20"}
        if roll in named_rolls:
            roll = named_rolls[roll]
            await ctx.send(f"Rolling {roll}")
        await ctx.send(parse_die.parse_die(roll))

    @commands.command(help="Admin only: Gets debug information")
    @commands.has_permissions(administrator=True)
    async def what(self, ctx):
        await ctx.author.send(file=discord.File(os.path.join(basic_paths.ROOT, "discord.log")))
        await ctx.author.send(file=discord.File(basic_paths.rjoin("groups/groups.yml")))

    async def hilfe(self, ctx):
        result = """
        ```
        **Generelle Befehle:**
          card Nimmt einen Namen entgegen. Sendet ein Bild der angegebenen Regelkarte.
          halloilaris Begrüßt den Ilaris Bot
          ilaris Nimmt eine Zahl oder einen Namen entgegen. Postet die entsprechende Seite im Regelwerk oder Regel.
          r Würfelt. 
          what Nur für Administratoren: Ruft Debug-Informationen ab
        **Gruppen Befehle:**
          gcreate Erzeugt eine neue Gruppe mit dir als GM.
          gdestroy Zerstört eine Gruppe, die du erstellt hast.
          gjoin Tritt einer Gruppe als maximum_players bei
          gleave Verlasse eine Gruppe als maximum_players
          glist Listet alle beitretbaren Gruppen auf.
          gremove Entfernt einen maximum_players aus deiner Gruppe
          gset Setzt einen Gruppenschlüssel.
          gsetdate Setzt das Datum.
          gsetdescription Setzt die Beschreibung.
          gsetnumberofplayers Setzt die Anzahl der maximum_players.

        Gib !help command ein, um weitere Informationen zu einem Befehl auf Englisch zu erhalten
        ```
        """
        await ctx.send(result)
