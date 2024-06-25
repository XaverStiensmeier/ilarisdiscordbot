import aiohttp
import json
from discord.ext import commands
from discord import Embed

class Client:
    """Client to interact with the Ilaris Online API.
    This is fairly trivial right now (just getting json from url). But it might become
    more features like authentication, searching, caching etc..
    """
    def __init__(self):
        print("init")
        self.base_url = "https://ilaris-online.de/api/"
        self.headers = {
            "Content-Type": "application/json",
        }
        self.session = aiohttp.ClientSession()
    
    async def get(self, endpoint):
        """GET request to the API."""
        print("get")
        url = f"{self.base_url}/{endpoint}"
        async with self.session.get(url, headers=self.headers) as response:
            if response.status != 200:
                response.raise_for_status()  # raise exception by status code of api
            print("respond")
            return await response.json()
    

    async def search_kreatur(self, search):
        data = await self.get(f"ilaris/kreatur/?search={search}")
        # NOTE: discord fails for content > 2000 chars
        # TODO: create a custom api view for this to save some traffic
        short_data = [{"id": data["id"], "name": data["name"]} for data in data]
        print(short_data)
        return short_data
    

    async def kreatur_embed(self, id, close=True):
        data = await self.get(f"ilaris/kreatur/{id}")
        print(data)
        embed = Embed(
            title=data["name"],
            # description=data["description"],
            # color=discord.Color.green()
        )
        if close:
            self.session.close()
        return embed