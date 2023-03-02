#!/usr/bin/env python3
# Imports
import signal
import sys

import yaml

import basic_paths

PLAYER_NUMBER = "spieleranzahl"
DATE = "uhrzeit"
DESCRIPTION = "beschreibung"
PLAYER = "spieler"


def save_groups_yaml(path="groups/groups.yml"):
    with open(basic_paths.rjoin(path), "w+") as yaml_file:
        yaml.safe_dump(groups, yaml_file)


def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

ALLOWED_KEYS = [DATE, PLAYER_NUMBER, DESCRIPTION]

with open(basic_paths.rjoin("groups/groups.yml"), "r") as yaml_file:
    groups = yaml.safe_load(yaml_file) or {}


def list_groups(show_full=False):
    return_str = "**- Gruppen Liste -**\n"
    return_strs = [return_str]
    for group, daten in groups.items():
        return_str = ""
        if show_full or len(daten[PLAYER]) < int(daten[PLAYER_NUMBER]):
            return_str += f"**--- {group} ---**\n"
            return_str += f"{DESCRIPTION}: {daten[DESCRIPTION]}\n"
            return_str += f"{DATE}: {daten[DATE]}\n"
            return_str += f"{PLAYER_NUMBER}: ({len(daten[PLAYER])}/{daten[PLAYER_NUMBER]})\n"
            return_str += f"Zum Beitreten: `!gjoin {group}`\n\n"
            return_strs.append(return_str)
    return return_strs


def create_group(group, date, player_number=4, description=""):
    if groups.get(group):
        return 0, "Deine Gruppe existiert bereits."
    groups[group] = {DATE: date, PLAYER_NUMBER: player_number, DESCRIPTION: description, PLAYER: []}
    return_str = f"Neue Gruppe {group} angelegt.\n"
    return_str += f"Zum Gruppe entfernen: `!gdestroy {'_'.join(group.split('_')[:-1])}`\n"
    return_str += f"Zum Beitreten: `!gjoin {group}`\n\n"
    return True, return_str


def destroy_group(group):
    if groups.get(group):
        group = groups.pop(group)
        return 1, "Deine Gruppe wurde gelöscht.", group[PLAYER]
    return False, "Deine Gruppe existiert nicht.", []


def set_key(group, key, value):
    if groups.get(group):
        if key in ALLOWED_KEYS:
            groups[group][key] = value
            return f"{key}: '{value}' wurde gesetzt"
        else:
            return f"{key} konnte nicht gesetzt werden."
    else:
        return f"Gruppe {group} existiert nicht."


def remove_player(gruppe, player):
    if groups.get(gruppe):
        if player in groups[gruppe][PLAYER]:
            groups[gruppe][PLAYER].remove(player)
            return True, f"Spieler {player} wurde entfernt."
        else:
            return False, f"Spieler {player} ist nicht in Gruppe {gruppe}."
    else:
        return False, f"Gruppe {gruppe} existiert nicht."


def add_self(group, player):
    if groups.get(group):
        if player not in groups[group][PLAYER]:
            current_player_number = len(groups[group][PLAYER])
            maximum_player_number = int(groups[group][PLAYER_NUMBER])
            if current_player_number < maximum_player_number:
                groups[group][PLAYER].append(player)
                return_str = f"Du wurdest Gruppe {group} hinzugefügt.\n"
                return_str += f"Zum Verlassen `!gleave {group}`"
                return True, return_str
            else:
                return False, f"Gruppe {group} ist bereits voll: {current_player_number}/{maximum_player_number}"
        else:
            return False, f"Du bist bereits Teil der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


def remove_self(group, player):
    if groups.get(group):
        if player in groups[group][PLAYER]:
            groups[group][PLAYER].remove(player)
            return True, f"Du wurdest aus Gruppe {group} entfernt."
        else:
            return False, f"Du bist kein Spieler der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."
