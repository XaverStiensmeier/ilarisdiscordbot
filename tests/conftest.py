import discord
import discord.ext.commands as commands
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
import config

# import commands we want to test
from cogs.generalCog import GeneralCommands
from cogs.groupsCog import GroupCommands

# provide a bot instance to be used in all tests
@pytest_asyncio.fixture
async def bot():
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