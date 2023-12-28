#!/usr/bin/env python3
# Imports
import signal
import sys
import os

import yaml

PLAYER_NUMBER = "spieleranzahl"
DATE = "uhrzeit"
DESCRIPTION = "beschreibung"
PLAYER = "spieler"
GROUPS_PATH = os.path.join("resources", "groups.yml")


def save_groups_yaml(guild):
    with open(GROUPS_PATH, "w+") as file:
        yaml.safe_dump(groups, file)


def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

groups = {}

ALLOWED_KEYS = [DATE, PLAYER_NUMBER, DESCRIPTION]

# LOAD GROUPS
if os.path.isfile(GROUPS_PATH):
    with open(GROUPS_PATH, "r") as yaml_file:
        groups = yaml.safe_load(yaml_file)


def list_groups(guild, show_full=False):
    guild_groups = groups.get(guild, {})
    return_str = "**\- Gruppen Liste -**\n"
    return_strs = [return_str]
    for group, daten in guild_groups.items():
        return_str = ""
        if show_full or len(daten[PLAYER]) < int(daten[PLAYER_NUMBER]):
            return_str += f"**--- {group} ---**\n"
            return_str += f"{DESCRIPTION}: {daten[DESCRIPTION]}\n"
            return_str += f"{DATE}: {daten[DATE]}\n"
            return_str += f"{PLAYER_NUMBER}: ({len(daten[PLAYER])}/{daten[PLAYER_NUMBER]})\n"
            return_str += f"Zum Beitreten: `!gjoin {group}`\n\n"
            return_strs.append(return_str)
    return return_strs


def create_group(guild, group, date, player_number=4, description=""):
    guild_groups = groups.get(guild, {})
    if guild_groups.get(group):
        return False, "Deine Gruppe existiert bereits."
    guild_groups[group] = {DATE: date, PLAYER_NUMBER: player_number, DESCRIPTION: description, PLAYER: []}
    return_str = f"Neue Gruppe {group} angelegt.\n"
    return_str += f"Zum Gruppe entfernen: `!gdestroy {'_'.join(group.split('_')[:-1])}`\n"
    return_str += f"Zum Beitreten: `!gjoin {group}`\n\n"
    return True, return_str


def destroy_group(guild, group):
    guild_groups = groups.get(guild, {})
    if guild_groups.get(group):
        group_dict = guild_groups.pop(group)
        return 1, "Deine Gruppe wurde gelöscht.", group_dict[PLAYER]
    return False, "Deine Gruppe existiert nicht.", []


def set_key(guild, group, key, value):
    guild_groups = groups.get(guild, {})
    if guild_groups.get(group):
        if key in ALLOWED_KEYS:
            guild_groups[group][key] = value
            return f"{key}: '{value}' wurde gesetzt"
        else:
            return f"{key} konnte nicht gesetzt werden."
    else:
        return f"Gruppe {group} existiert nicht."


def remove_player(guild, group, player):
    guild_groups = groups.get(guild, {})
    if guild_groups.get(group):
        if player in guild_groups[group][PLAYER]:
            guild_groups[group][PLAYER].remove(player)
            return True, f"Spieler {player} wurde entfernt."
        else:
            return False, f"Spieler {player} ist nicht in Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


def add_self(guild, group, player):
    guild_groups = groups.get(guild, {})
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


def remove_self(guild, group, player):
    guild_groups = groups.get(guild, {})
    if guild_groups.get(group):
        if player in guild_groups[group][PLAYER]:
            guild_groups[group][PLAYER].remove(player)
            return True, f"Du wurdest aus Gruppe {group} entfernt."
        else:
            return False, f"Du bist kein Spieler der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."
