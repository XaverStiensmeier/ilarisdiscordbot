#!/usr/bin/env python3
import os

import discord
from discord.ext import commands

import basic_paths
from cogs.general import differ
from cogs.general import ilaris_database
from cogs.general import parse_die

cards = [os.path.splitext(filename)[0] for filename in os.listdir(basic_paths.rjoin("manoeverkarten"))]

GERMAN_HELP = """```
Generelle Befehle:
  card Nimmt einen Namen entgegen. Sendet ein Bild der angegebenen Regelkarte.
  halloilaris Begrüßt den Ilaris Bot
  ilaris Nimmt eine Zahl oder einen Namen entgegen. Postet die entsprechende Seite im Regelwerk oder Regel.
  r Würfelt. Bspw. 2w6+3 wird zu 'Gib die Summe aus 2 geworfenen 6-seitigen Würfeln und 3 zurück'. Besonders:
    I: Gibt 1w20 zurück. I+: Mit Schicksalspunkt. II+: Mit Schicksalspunkt und Eigenheit.
    III: Gibt 2@3w20 zurück. III+: Mit Schicksalspunkt. III++: Mit Schicksalspunkt und Eigenheit.
  what Nur für Admins: Ruft Debug-Informationen ab
Gruppen Befehle:
  gcreate Nimmt Gruppenname Datum "Maximale Spieleranzahl" und Beschreibung entgegen. Erzeugt eine neue Gruppe mit dir als GM. 
  gdestroy Nimmt Gruppennamen (ohne deinen Nutzernamen) entgegen. Zerstört diese Gruppe, die du erstellt hast.
  gjoin Nimmt Gruppennamen entgegen. Betritt diese Gruppe.
  gleave Nimmt Gruppennamen entgegen. Verlässt diese Gruppe.
  glist Listet alle beitretbaren Gruppen auf. Nimmt optional "True" entgegen und zeigt dann auch volle Gruppen an.
  gremove Nimmt Gruppennamen (ohne deinen Nutzernamen) und Nutzernamen des Spielers entgegen. Entfernt diesen Spieler aus deiner Gruppe.
  gset Nimmt Gruppennamen (ohne deinen Nutzernamen), ein Attribut und einen Wert entgegen. Weißt dem Attribut den Wert zu.
  gsetdate Nimmt Gruppennamen (ohne deinen Nutzernamen) und Datum entgegen. Setzt das Datum.
  gsetdescription Nimmt Gruppennamen (ohne deinen Nutzernamen) und Beschreibung entgegen. Setzt die Beschreibung.
  gsetnumberofplayers Nimmt Gruppennamen (ohne deinen Nutzernamen) und maximale Spieler entgegen. Setzt die Anzahl der maximalen Spieler.

Gib !help command ein, um weitere Informationen zu einem Befehl auf Englisch zu erhalten
Anmerkung: Argumente mit Leerzeichen müssen in Anführungszeichen angegeben werden: "Das ist ein Argument"
```
"""

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

    @commands.command(help="Prints a German simplified help page")
    async def hilfe(self, ctx):
        await ctx.send(GERMAN_HELP)
