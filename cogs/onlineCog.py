
import logging
import discord
from discord import app_commands, Interaction, SelectMenu, SelectOption
from discord.ext import commands
from discord.ui import TextInput, Select, View
from config import DATA, settings, messages as msg
from cogs.ilarisonline.api import Client


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
            if len(matches) == 1:
                kid = matches[0]["id"]
            elif len(matches) > 1:
                print(matches)
                view = View()
                view.add_item(KreaturSelect(inter, matches))
                await inter.response.send_message(
                    f"Es gibt mehrere Treffer:\n",
                    view=view,
                    ephemeral=True
                )
                return
        # answer kreatur by id
        embed = await api.kreatur_embed(kid)
        await inter.response.send_message("Da: ", embed=embed)
        return


class KreaturSelect(Select):
    def __init__(self, inter, creatures):
        self.inter = inter
        options = [SelectOption(label=c['name'], value=c['id']) for c in creatures]
        super().__init__(
            placeholder="Choose a creature...",
            min_values=1, max_values=1, options=options)
    
    async def callback(self, inter: discord.Interaction) -> None:
        # await inter.response.defer() # processing it wihtout sending reply
        c_id = inter.data['values'][0]
        api = Client()
        embed = await api.kreatur_embed(c_id)
        await inter.response.send_message("", embed=embed)  # followup to avoid quote
        # await self.inter.response.delete_message()
