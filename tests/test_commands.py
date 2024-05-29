import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
# from messages import msg

from cogs.generalCog import GeneralCommands
from cogs.groupsCog import GroupCommands


# NOTE this bot instance is required by dpytest, we can move it somewhere later
@pytest_asyncio.fixture
async def bot():
    # Setup new bot instance for testing
    bot = commands.Bot(
        command_prefix="!",
        intents=discord.Intents.all())
    await bot._async_setup_hook()  # setup the loop
    # Add all cogs we want to test here:
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(GroupCommands(bot))
    dpytest.configure(bot)
    yield bot  # tests are applied here on this bot instance
    # Clean up when tests are done
    await dpytest.empty_queue()


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
    assert dpytest.verify().message().contains().content("Details:")