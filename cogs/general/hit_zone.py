#!/usr/bin/env python3
"""Optional rule Trefferzonen (hit zones), see Ilaris p. 33.

The hit zone is rolled with 1d6. Zone names, checks and effects are part of
the messages (hit_zones), keyed by the d6 result.
"""
import random

from config import messages as msg


def roll_hit_zone():
    """Returns the d6 result and the matching zone from the messages."""
    d6 = random.randint(1, 6)
    return d6, msg["hit_zones"][d6]


def add_hit_zone_fields(embed, d6, zone):
    """Adds the hit zone and its wound pain check to a roll embed."""
    embed.add_field(
        name=f"🎯 {msg['hit_zone_title']}",
        value=f"{zone['emoji']} **{zone['name']}** ({msg['hit_zone_die']}: {d6})",
        inline=True,
    )
    embed.add_field(
        name=f"💢 {msg['hit_zone_pain']}",
        value=f"{zone['check']} (20, I): {zone['effect']}",
        inline=True,
    )
    return embed
