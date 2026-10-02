""" Button to roll a hit zone for an existing roll result

Optional rule Trefferzonen (Ilaris p. 33). The button is shown below every
roll result, rolls 1d6 once and adds the hit zone to the embed.
"""

from __future__ import annotations

import discord

from config import messages as msg
from cogs.general import hit_zone
from views.base import BaseView


class HitZoneView(BaseView):

    def __init__(self, user: discord.User | discord.Member, embed: discord.Embed, timeout: float = 600.0):
        super().__init__(user, timeout=timeout)
        self.embed = embed

    @discord.ui.button(label=msg["hit_zone_button"], emoji="🎯", style=discord.ButtonStyle.secondary)
    async def roll_hit_zone(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        hit_zone.add_hit_zone_fields(self.embed, *hit_zone.roll_hit_zone())
        # the hit zone is rolled only once per result
        self._disable_all()
        await interaction.response.edit_message(embed=self.embed, view=self)
        self.stop()

    async def on_timeout(self) -> None:
        try:
            await super().on_timeout()
        except discord.NotFound:
            pass  # result was already deleted (❌ reaction)
