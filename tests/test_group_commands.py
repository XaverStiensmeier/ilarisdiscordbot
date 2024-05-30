import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
# from messages import msg

# bot fixture is defined in conftest.py and automatically provided by pytest


@pytest.mark.asyncio
async def test_helloilaris(bot):
    await dpytest.message("!glist")
    assert dpytest.verify().message()