#!/usr/bin/env python3
# Imports
import signal
import sys

import yaml

import basic_paths

PLAYER_NUMBER = "spielerzahl"
DATE = "uhrzeit"
DESCRIPTION = "beschreibung"
PLAYER = "spieler"


def sigterm_handler(_signo, _stack_frame):
    with open(basic_paths.rjoin("gruppen/gruppen.yml"), "w+") as yaml_file:
        yaml.safe_dump(gruppen, yaml_file)
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

ALLOWED_KEYS = [DATE, PLAYER_NUMBER, DESCRIPTION]

with open(basic_paths.rjoin("gruppen/gruppen.yml"), "r") as yaml_file:
    gruppen = yaml.safe_load(yaml_file) or {}


def list_groups(show_full=False):
    return_str = "**- Gruppen Liste -**\n"
    for gruppe, daten in gruppen.items():
        if show_full or len(daten[PLAYER]) < daten[PLAYER_NUMBER]:
            return_str += f"**--- {gruppe} ---**\n"
            return_str += f"{DESCRIPTION}: {daten[DESCRIPTION]}\n"
            return_str += f"{DATE}: {daten[DATE]}\n"
            return_str += f"{PLAYER_NUMBER}: ({len(daten[PLAYER])}/{daten[PLAYER_NUMBER]})\n\n"
    return return_str


def create_group(group, date, player_number=4, description=""):
    if gruppen.get(group):
        return 0, "Deine Gruppe existiert bereits."
    gruppen[group] = {DATE: date, PLAYER_NUMBER: player_number, DESCRIPTION: description, PLAYER: []}
    return True, f"Neue Gruppe {group} angelegt."


def destroy_group(group):
    if gruppen.get(group):
        gruppen.pop(group)
        return 1, "Deine Gruppe wurde gelöscht."
    return False, "Deine Gruppe existiert nicht."


def set_key(group, key, value):
    if gruppen.get(group):
        if key in ALLOWED_KEYS:
            gruppen[group][key] = value
            return f"{key}: {value} wurde gesetzt"
        else:
            return f"{key} konnte nicht gesetzt werden."
    else:
        return f"Gruppe {group} existiert nicht."


def remove_player(gruppe, player):
    if gruppen.get(gruppe):
        if player in gruppen[gruppe][PLAYER]:
            gruppen[gruppe][PLAYER].remove(player)
            return True, f"Spieler {player} wurde entfernt."
        else:
            return False, f"Spieler {player} ist nicht in Gruppe {gruppe}."
    else:
        return False, f"Gruppe {gruppe} existiert nicht."


def add_self(group, player):
    if gruppen.get(group):
        if player not in gruppen[group][PLAYER]:
            aktuelle_anzahl = len(gruppen[group][PLAYER])
            maximal_anzahl = gruppen[group][PLAYER_NUMBER]
            if aktuelle_anzahl < maximal_anzahl:
                gruppen[group][PLAYER].append(player)
                return True, f"Du wurdest Gruppe {group} hinzugefügt."
            else:
                return False, f"Gruppe {group} ist bereits voll: {aktuelle_anzahl}/{maximal_anzahl}"
        else:
            return False, f"Du bist bereits Teil der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


def remove_self(group, player):
    if gruppen.get(group):
        if player in gruppen[group][PLAYER]:
            gruppen[group][PLAYER].remove(player)
            return True, f"Du wurdest aus Gruppe {group} entfernt."
        else:
            return False, f"Du bist kein Spieler der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."
