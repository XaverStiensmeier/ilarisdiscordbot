import aiohttp
import json
from discord.ext import commands


class Client:
    """Client to interact with the Ilaris Online API.
    This is fairly trivial right now (just getting json from url). But it might become
    more features like authentication, searching, caching etc..
    """
    def __init__(self):
        self.base_url = "https://ilaris-online.de/api/"
        self.headers = {
            "Content-Type": "application/json",
        }
        self.session = aiohttp.ClientSession()
    
    def ensure_session(self):
        """Creates new session if none is open anymore"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def auto_close(self, close):
        """Call on end of each request to make closing sessions more convenient."""
        if close and not self.session.closed:
            await self.session.close()
    
    async def get(self, endpoint, close=True):
        """GET request to the API."""
        self.ensure_session()
        url = f"{self.base_url}/{endpoint}"
        async with self.session.get(url, headers=self.headers) as response:
            if response.status != 200:
                await self.auto_close(close)
                response.raise_for_status()  # raise exception by status code of api
            data = await response.json()
        await self.auto_close(close)
        return data
    
    async def search_kreatur(self, search):
        """Uses api search (name and desc). returns list of matches from database.
        # TODO: create a custom api view with only name/id to save some traffic
        """
        self.ensure_session()
        data = await self.get(f"ilaris/kreatur/?search={search}")
        short_data = [{"id": data["id"], "name": data["name"]} for data in data]
        return short_data
