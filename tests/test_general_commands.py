import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
# from messages import msg


@pytest.mark.asyncio
async def test_helloilaris(bot):
    await dpytest.message("!helloilaris")
    assert dpytest.verify().message().contains().content("Hey, ")


@pytest.mark.asyncio
async def test_creatures(bot):
    await dpytest.message("!creatures")
    assert dpytest.verify().message().contains().content("https://ilaris-online.de/")


@pytest.mark.asyncio
async def test_r(bot):
    await dpytest.message("!r")
    assert dpytest.verify().message()