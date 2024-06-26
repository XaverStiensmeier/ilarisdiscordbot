
import logging
import discord
from discord import app_commands
from discord.ext import commands
from config import DATA, settings, messages as msg
from cogs.ilarisonline.api import Client
from ui.views import KreaturSelect, kreatur_embed


class OnlineCog(commands.Cog):
    """A set of commands with ilaris-online api calls.
    """
    group = app_commands.Group(name="io", description="Ilaris Online API") # guild_only=True

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    

    @group.command(name="kreatur", description="Findet Kreaturen auf ilaris-online.de")
    async def iocreature(self, inter, suche: str):
        try:
            kid = int(suche)
        except ValueError:
            kid = None
        api = Client()
        if not kid:  # search for kreatur by name
            matches = await api.search_kreatur(suche)
            if len(matches) == 0:
                await inter.response.send_message("Hab leider nichts gefunden.", ephemeral=True)
                return
            if len(matches) == 1:
                kid = matches[0]["id"]
            elif len(matches) > 1:
                view = KreaturSelect(inter, matches).as_view()
                await inter.response.send_message(
                    f"Es gibt mehrere Treffer:\n",
                    view=view,
                    ephemeral=True
                )
                return
        # answer kreatur by id
        data = await api.get(f"ilaris/kreatur/{kid}")
        embed = kreatur_embed(data)
        await inter.response.send_message("", embed=embed)
        return


