from discord import SelectOption, Interaction, Embed
from discord.ui import TextInput, View, Select
from cogs.ilarisonline.api import Client
from utility. sanitizer import cap


class KreaturSelect(Select):
    def __init__(self, inter, creatures):
        self.inter = inter
        options = [SelectOption(label=c['name'], value=c['id']) for c in creatures]
        super().__init__(
            placeholder="Choose a creature...",
            min_values=1, max_values=1, options=options)
    
    def as_view(self):
        return View().add_item(self)
    
    async def callback(self, inter: Interaction) -> None:
        c_id = inter.data['values'][0]
        api = Client()
        data = await api.get(f"ilaris/kreatur/{c_id}")
        embed = kreatur_embed(data)
        await inter.response.send_message("", embed=embed)  # followup to avoid quote
        # await self.inter.response.delete_message()


def kreatur_embed(data, as_view=False):
        """generates a discord embed from kreatur dict."""
        embed = Embed(
            title=data["name"],
            description=cap(data["kurzbeschreibung"]),
        )
        embed.set_thumbnail(url=f"https://ilaris-online.de/static/bilder/kreaturen/{data['typ']}.png")
        # EIGENSCHAFTEN
        # eigs = []
        # for e in data.get("eigenschaften", []):
        #     eig_str = e["name"]
        #     eig_str += f' ({cap(e["text"], 150)})' if e["text"] else ""
        #     eigs.append(eig_str)
        # NOTE: some eigs. have a lot of text.. we should shorten them or just show names
        eigs = [e["name"] for e in data.get("eigenschaften", []) if e["kategorie"] != "Info"]
        eigs = cap(", ".join(eigs))  # discord limit for items is 1024 chars
        if eigs:
            embed.add_field(name="Eigenschaften", value=eigs, inline=False)
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
        # INFOS
        for info in data.get("eigenschaften", []):
            if info["kategorie"] != "Info":
                continue
            text = cap(info.get("text", ""))
            embed.add_field(name=info["name"], value=text, inline=False)
        # SEND RESULT
        if as_view:
            view = View()
            view.add_item(embed)
            return view
        return embed