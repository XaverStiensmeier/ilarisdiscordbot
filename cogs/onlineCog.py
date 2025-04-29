
import logging
import discord
from discord import app_commands, Embed
from discord.ext import commands
from discord.ui import View
from config import DATA, settings, messages as msg
from cogs.ilarisonline.api import Client
from ui.views import ItemSelect
from utility.sanitizer import cap


class ItemPicker():
    """Base class that can be modified for individual API tables."""
    table = None
    id_key = "id"
    selector = ItemSelect

    def __init__(self, callback=None):
        self.api = Client()
        self.endpoint = f"ilaris/{self.table}/"
        self.selct_callback = callback
    
    async def load(self):
        """loads data for specific id from api"""
        self.data = await self.api.get(f"{self.endpoint}{self.id}")
    
    async def search(self, query):
        """searches api and returns all matches"""
        self.matches = await self.api.get(f"{self.endpoint}?search={query}")
    
    async def run(self, inter, query):
        """runs the search and returns the result"""
        # self.try_id(query)  # add id as search field in the api instead?
        await self.search(query)
        if len(self.matches) == 0:
            await inter.response.send_message("Hab leider nichts gefunden.", ephemeral=True)
        if len(self.matches) == 1:
            self.id = self.matches[0][self.id_key]
            await self.load()
            await inter.response.send_message("", embed=self.as_embed())
        elif len(self.matches) > 1:
            await self.select_match(inter, self.matches)
        return
    
    async def select_match(self, inter, matches):
        """pick an ID from multiple matches using any selector class"""
        menu = self.selector(inter, matches, pk=self.id_key)
        async def callback(inter):  # exceuted when user selects an item
            self.id = inter.data['values'][0]
            await self.load()
            await inter.response.send_message("", embed=self.as_embed())
        menu.callback = callback  # assign callback to dropdown menu
        await inter.response.send_message(
            f"Es gibt mehrere Treffer:\n",
            view=menu.as_view(),
            ephemeral=True
        )
        return

    def as_embed(self):
        """Overwrite this method for custom embeds."""
        raise NotImplementedError


class VorteilPicker(ItemPicker):
    table = "vorteil"
    id_key = "alias"
    
    def as_embed(self):
        """generates a discord embed from kreatur dict."""
        data = self.data
        embed = Embed(
            title=data["name"],
            description=cap(data["text"]),
        )
        # this fields are small and could be inlines
        if data.get("kosten") is not None:  # could be 0
            embed.add_field(name="Kosten:", value=data["kosten"])
        if data.get("typ"):
            embed.add_field(name="Kategorie:", value=data["typ"])
        if data.get("voraussetzungen", {}).get("text"):
            embed.add_field(name="Voraussetzungen:", value=data["voraussetzungen"]["text"])
        if data.get("effekt"):
            embed.add_field(name="Effekt:", value=data["effekt"]) 
        return embed


class ZauberPicker(ItemPicker):
    table = "zauber"
    id_key = "alias"

    def as_embed(self):
        data=self.data
        embed = Embed(
            title=data["name"],
            description=cap(data["text"]),
        )
        zferts = cap("\n".join(data.get("zauberfertigkeiten", [])))
        if zferts:
            embed.add_field(name="Fertigkeiten:", value="\n".join(data["zauberfertigkeiten"]))
        kost = cap(data.get("kosten"))
        if kost:
            embed.add_field(name="Kosten:", value=kost+"AsP")
        lernk = cap(data.get("lernkosten"))
        if lernk:
            embed.add_field(name="Lernkosten:", value=lernk+"EP")
        kinfo = cap(data.get("kosteninfo"))
        if kinfo:
            embed.add_field(name="Kosteninfo:", value=kinfo)
        return embed


class KreaturPicker(ItemPicker):
    table = "kreatur"
    
    def as_embed(self):
        """generates a discord embed from kreatur dict."""
        data = self.data
        embed = Embed(
            title=data["name"],
            description=cap(data["kurzbeschreibung"]),
            url=f"https://ilaris-online.de/app/kreatur/{data['id']}",
        )
        embed.set_thumbnail(url=f"https://ilaris-online.de/static/bilder/kreaturen/{data['typ']}.png")
        # EIGENSCHAFTEN
        # NOTE: some eigs. have a lot of text.. we should shorten them or just show names
        eigs = [e["name"] for e in data.get("eigenschaften", []) if e["kategorie"] != "Info"]
        eigs = cap(", ".join(eigs))  # discord limit for items is 1024 chars
        if eigs:
            embed.add_field(name="Eigenschaften", value=eigs, inline=False)
        # WERTE (kampf + attribute + energien in one field)
        kws = []
        for key, val in data.get("kampfwerte", {}).items():
            if not val or "label" in key:
                continue
            if key == "GST":
                kws.append(f'`GS {data["kampfwerte"]["GST_label"]}: {val}`')
            if key == "GSS":
                kws.append(f'`GS {data["kampfwerte"]["GSS_label"]}: {val}`')
            else:
                kws.append(f"`{key}: {val}`")
        for e in ["asp", "gup", "kap"]:
            if data.get(e):
                kws.append(f"`{e.upper()}: {data[e]}`")
        kws = cap(" ".join(kws))
        attrs = [f"`{k}: {v}`" for k, v in data.get("attribute", {}).items() if v]
        attrs = cap(" ".join(attrs))
        ka_values = "\n".join([kws, attrs])
        if kws or attrs:
            embed.add_field(name="Werte", value=ka_values, inline=False)
        # ANGRIFFE
        angs = []
        for a in data.get("angriffe", []):
            ang_str = a["name"] + ": "
            ang_eigs = a.pop("eigenschaften", '')
            keys = ["rw", "at", "vt", "tp"]
            ang_str += " ".join([f"`{k.upper()}: {a.get(k, '')}`" for k in keys])
            if ang_eigs:
                # non-breaking space
                ang_str += f"\n\u00A0\u00A0\u00A0\u00A0_{cap(ang_eigs, 300)}_"
            angs.append(ang_str)
        angs_str = cap("\n".join(angs))
        embed.add_field(name="Angriffe", value=angs_str, inline=False)
        # FERTIGKEITEN
        ferts = [f'{t["name"]} `{t["wert"]}`' for t in data.get("freietalente", [])]
        ferts = cap(", ".join(ferts))
        if ferts:
            embed.add_field(name="Fertigkeiten", value=ferts, inline=False)
        # ZAUBER
        zfs = []
        for zf in data.get("zauberfertigkeiten", []):
            zf_str = f'{zf["name"]} `{zf["wert"]}`: '
            zaubs = ", ".join([z["name"] for z in zf.get("zaubers", [])])
            zf_str += zaubs
            zfs.append(zf_str)
        zfs = cap("\n".join(zfs))
        if zfs:
            embed.add_field(name="Übernatürliches", value=zfs, inline=False)
        # INFOS (one field per info)
        for info in data.get("eigenschaften", []):
            if info["kategorie"] != "Info":
                continue
            text = cap(info.get("text", ""))
            embed.add_field(name=info["name"], value=text, inline=False)
        return embed


class OnlineCog(commands.Cog):
    """A set of commands with ilaris-online api calls.
    """
    group = app_commands.Group(name="io", description="Ilaris Online API") # guild_only=True

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @group.command(name="vorteil", description="Findet Vorteile von ilaris-online.de")
    async def iovorteil(self, inter, suche: str):
        picker = VorteilPicker(inter)
        await picker.run(inter, suche)

    @group.command(name="zauber", description="Findet Zauber von ilaris-online.de")
    async def iovorteil(self, inter, suche: str):
        picker = ZauberPicker(inter)
        await picker.run(inter, suche)

    @group.command(name="kreatur", description="Findet Kreaturen auf ilaris-online.de")
    async def iokreatur(self, inter, suche: str):
        picker = KreaturPicker(inter)
        await picker.run(inter, suche)

