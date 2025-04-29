from discord import SelectOption, Interaction, Embed
from discord.ui import TextInput, View, Select
from cogs.ilarisonline.api import Client
from utility. sanitizer import cap



class ItemSelect(Select):
    def __init__(self, inter, items, pk="id"):
        self.inter = inter
        options = [SelectOption(label=i['name'], value=i[pk]) for i in items]
        super().__init__(
            placeholder="Choose an item...",
            min_values=1, max_values=1, options=options)
    
    def as_view(self):
        return View().add_item(self)

