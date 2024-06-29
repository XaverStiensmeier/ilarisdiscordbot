from discord import SelectOption, Interaction, Embed, ButtonStyle
from discord.ui import TextInput, View, Select, button
from cogs.ilarisonline.api import Client
from utility.sanitizer import cap
from config import messages as msg



class ItemSelect(Select):
    def __init__(self, inter, items, pk="id"):
        self.inter = inter
        options = [SelectOption(label=i['name'], value=i[pk]) for i in items]
        super().__init__(
            placeholder="Choose an item...",
            min_values=1, max_values=1, options=options)
    
    def as_view(self):
        return View().add_item(self)


class HpButtons(View):

    def __init__(self, name):
        super().__init__(timeout=None)
        self.name = name
        self.wounds = 0
        self.user = None

    def embed(self):
        bar = self.wounds * "❌"
        text = f"{self.wounds} Wunden\n{bar}"
        if self.wounds > 2:
            text += f"\nProben: -{(self.wounds-2)*2}"
        return Embed(title=self.name, description=text)

    async def update(self, inter: Interaction):
        embed = self.embed()
        await inter.response.edit_message(embed=embed, view=self)
        
    @button(label="+1", emoji="❌")
    async def join(self, inter: Interaction, button) -> None:
        self.wounds += 1 if self.wounds < 9 else 0
        await self.update(inter)

    @button(label="-1", emoji="💚")
    async def reduce(self, inter: Interaction, button) -> None:
        self.wounds -=1 if self.wounds > 0 else 0
        await self.update(inter)
    
    @button(label="", emoji="🗑️")
    async def reset(self, inter: Interaction, button) -> None:
        await inter.response.defer()
        await inter.delete_original_response()