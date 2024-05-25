#!/usr/bin/env python3
# Imports
import signal
import sys
import os
import logging

from filelock import FileLock
import yaml

PLAYER_NUMBER = "player_number"
PLAYER_NUMBER_PRINT = "Spielerzahl"
DATE = "date"
DATE_PRINT = "Datum"
DESCRIPTION = "description"
DESCRIPTION_PRINT = "Beschreibung"
PLAYER = "player"
PLAYER_PRINT = "Beschreibung"
GROUPS_PATH = os.path.join("resources", "groups.yml")
CHANNELS = "channels"
CATEGORY = "category"
OWNER = "owner"

HOW_TO_JOIN = """
Wo du beitreten möchtest, kopiere den Teil mit `!gjoin` und sendet diese Zeile dann in #bot-spam. 
Der Bot sorgt automatisch für die Zuordnung :wink:

Bei Schwierigkeiten, einfach fragen. Wir helfen, wo wir können!
_ _
"""


def save_yaml(original_function):
    def wrapper(guild, *args, **kwargs):
        result = original_function(guild, *args, **kwargs)
        with open(GROUPS_PATH, "w+") as file:
            logging.debug(f"Saving triggered by {guild}...")
            with FileLock("groups.yml.lock"):
                yaml.safe_dump(groups, file)
        return result

    return wrapper


@save_yaml
def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

groups = {}

ALLOWED_KEYS = [DATE, PLAYER_NUMBER, DESCRIPTION]

# LOAD GROUPS
if os.path.isfile(GROUPS_PATH):
    with open(GROUPS_PATH, "r") as yaml_file:
        groups = yaml.safe_load(yaml_file) or {}


@save_yaml
def list_groups(guild, show_full=False):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    return_str = HOW_TO_JOIN
    return_str += "**\- Gruppen Liste -**\n"
    return_strs = [return_str]
    for group, daten in guild_groups.items():
        return_str = ""
        if show_full or len(daten[PLAYER]) < int(daten[PLAYER_NUMBER]):
            return_str += f"**{group.replace('-', ' ').title()}**\n"
            return_str += f"{daten[DESCRIPTION]}\n"
            return_str += f"**{DATE_PRINT}**: {daten[DATE]}\n"
            return_str += f"**{PLAYER_NUMBER_PRINT}**: {len(daten[PLAYER])}/{daten[PLAYER_NUMBER]}\n"
            return_str += f"**Zum Beitreten**: `!gjoin {group}`\n\n"
            return_str += "_ _"
            return_strs.append(return_str)
    return return_strs


@save_yaml
def create_group(guild, group, owner, category, date, player_number=4, description=""):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    guild_groups[group] = {OWNER: owner, CATEGORY: category, DATE: date, PLAYER_NUMBER: player_number,
                           DESCRIPTION: description,
                           PLAYER: [], CHANNELS: []}

    return_str = f"Neue Gruppe {group} angelegt.\n"
    return_str += f"Zum Channel hinzufügen: `!gaddchannel {'_'.join(group.split('_')[:-1])} new_channel`.\n"
    return_str += f"Zum Gruppe entfernen: `!gdestroy {'_'.join(group.split('_')[:-1])}`\n"
    return_str += f"Zum Beitreten: `!gjoin {group}`\n\n"
    return return_str


def group_exists(guild, group):
    return groups.get(guild) and groups[guild].get(group)


@save_yaml
def destroy_group(guild, group):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        group_dict = guild_groups.pop(group)
        return 1, "Die Gruppe wurde gelöscht.", group_dict[PLAYER], group_dict[CHANNELS], group_dict[CATEGORY]
    return False, "Die Gruppe existiert nicht.", [], [], []


def get_main_channel(guild, group):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        return guild_groups[group][CHANNELS][0]
    return None


@save_yaml
def set_key(guild, group, key, value):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        if key in ALLOWED_KEYS:
            guild_groups[group][key] = value
            return f"{key}: '{value}' wurde gesetzt"
        else:
            return f"{key} konnte nicht gesetzt werden."
    else:
        return f"Gruppe {group} existiert nicht."


@save_yaml
def remove_player(guild, group, player):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        if player in guild_groups[group][PLAYER]:
            guild_groups[group][PLAYER].remove(player)
            return True, f"Spieler <@{player}> wurde entfernt."
        else:
            return False, f"Spieler <@{player}> ist nicht in Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


@save_yaml
def add_self(guild, group, player):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        if player not in guild_groups[group][PLAYER]:
            current_player_number = len(guild_groups[group][PLAYER])
            maximum_player_number = int(guild_groups[group][PLAYER_NUMBER])
            if current_player_number < maximum_player_number:
                guild_groups[group][PLAYER].append(player)
                return_str = f"Du wurdest Gruppe {group} hinzugefügt.\n"
                return_str += f"Zum Verlassen `!gleave {group}`"
                return True, return_str
            else:
                return False, f"Gruppe {group} ist bereits voll: {current_player_number}/{maximum_player_number}"
        else:
            return False, f"Du bist bereits Teil der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


@save_yaml
def remove_self(guild, group, player):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        if player in guild_groups[group][PLAYER]:
            guild_groups[group][PLAYER].remove(player)
            return True, f"Du wurdest aus Gruppe {group} entfernt."
        else:
            return False, f"Du bist kein Spieler der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


@save_yaml
def add_channel(guild, group, channel):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        guild_groups[group][CHANNELS].append(channel)


@save_yaml
def remove_channel(guild, group, channel):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    if guild_groups.get(group):
        guild_groups[group][CHANNELS].remove(channel)


def channel_exists(guild, group, channel):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]

    return guild_groups.get(group) and channel in guild_groups[group][CHANNELS]


def is_owner(guild, group, author_id):
    if not groups.get(guild):
        groups[guild] = {}
    guild_groups = groups[guild]
    return guild_groups.get(group) and guild_groups[group][OWNER] == author_id
