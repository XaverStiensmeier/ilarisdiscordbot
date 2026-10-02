import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
import config
from unittest.mock import AsyncMock, MagicMock
from views.hit_zone import HitZoneView
from cogs.generalCog import is_plain_dice_roll
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
    embed = dpytest.get_message().embeds[0]
    assert embed.title.startswith("🎲")


@pytest.mark.asyncio
async def test_tp(bot):
    await dpytest.message("!tp 2w6+3 Säbel")
    embed = dpytest.get_message().embeds[0]
    assert embed.title.startswith("⚔️ Säbel")
    assert embed.title.endswith(" TP")
    zone_names = [zone["name"] for zone in config.messages["hit_zones"].values()]
    assert any(name in embed.fields[0].value for name in zone_names)


@pytest.mark.asyncio
async def test_hit_zone_button(bot):
    embed = discord.Embed(title="🎲 Ergebnis 11")
    view = HitZoneView(user=None, embed=embed)
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await view.roll_hit_zone.callback(interaction)
    zone_names = [zone["name"] for zone in config.messages["hit_zones"].values()]
    assert any(name in embed.fields[0].value for name in zone_names)
    assert view.roll_hit_zone.disabled
    assert view.is_finished()
    interaction.response.edit_message.assert_awaited_once_with(embed=embed, view=view)


@pytest.mark.parametrize("roll", ["2w6+3", "2d6", "1W20+4", "3d6-1", "1d20"])
def test_plain_dice_roll(roll):
    assert is_plain_dice_roll(roll)


@pytest.mark.parametrize("roll", ["I", "III", "IIIo", "Ioo+3", "2@3d20", "1@2w20+5", "5", ""])
def test_special_roll(roll):
    assert not is_plain_dice_roll(roll)
