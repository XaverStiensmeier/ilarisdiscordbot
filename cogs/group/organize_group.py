#!/usr/bin/env python3
# Imports
import signal
import sys

import yaml

import basic_paths


def sigterm_handler(_signo, _stack_frame):
    with open(basic_paths.rjoin("gruppen/gruppen.yml"), "w+") as yaml_file:
        yaml.safe_dump(gruppen, yaml_file)
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

ALLOWED_KEYS = ["uhrzeit", "spielerzahl", "beschreibung"]

with open(basic_paths.rjoin("gruppen/gruppen.yml"), "r") as yaml_file:
    gruppen = yaml.safe_load(yaml_file) or {}


def list_groups(show_full=False):
    return_str = "**- Gruppen Liste -**\n"
    for gruppe, daten in gruppen.items():
        if show_full or len(daten['spieler']) < daten['spielerzahl']:
            return_str += f"**--- {gruppe} ---**\n"
            return_str += f"Beschreibung: {daten['beschreibung']}\n"
            return_str += f"Uhrzeit: {daten['uhrzeit']}\n"
            return_str += f"Spielerzahl: ({len(daten['spieler'])}/{daten['spielerzahl']})\n\n"
    return return_str


def create_group(gruppe, uhrzeit, spielerzahl=4, beschreibung=""):
    if gruppen.get(gruppe):
        return 0, "Deine Gruppe existiert bereits."
    gruppen[gruppe] = {"uhrzeit": uhrzeit, "spielerzahl": spielerzahl, "beschreibung": beschreibung, "spieler": []}
    return True, f"Neue Gruppe {gruppe} angelegt."


def destroy_group(gruppe):
    if gruppen.get(gruppe):
        gruppen.pop(gruppe)
        return 1, "Deine Gruppe wurde gelöscht."
    return False, "Deine Gruppe existiert nicht."


def set_key(gruppe, key, value):
    if gruppen.get(gruppe) and key in ALLOWED_KEYS:
        gruppen[gruppe][key] = value
        return f"{key}: {value} wurde gesetzt"
    else:
        return f"{key} konnte nicht gesetzt werden."


def remove_player(gruppe, spieler):
    if gruppen.get(gruppe):
        if spieler in gruppen[gruppe]["spieler"]:
            gruppen[gruppe]["spieler"].remove(spieler)
            return True, f"Spieler {spieler} wurde entfernt."
        else:
            return False, f"Spieler {spieler} ist nicht in Gruppe {gruppe}."
    else:
        return False, f"Gruppe {gruppe} existiert nicht."


def add_self(gruppe, spieler):
    if gruppen.get(gruppe):
        if spieler not in gruppen[gruppe]["spieler"]:
            aktuelle_anzahl = len(gruppen[gruppe]["spieler"])
            maximal_anzahl = gruppen[gruppe]["spielerzahl"]
            if aktuelle_anzahl < maximal_anzahl:
                gruppen[gruppe]["spieler"].append(spieler)
                return True, f"Du wurdest Gruppe {gruppe} hinzugefügt."
            else:
                return False, f"Gruppe {gruppe} ist bereits voll: {aktuelle_anzahl}/{maximal_anzahl}"
        else:
            return False, f"Du bist bereits Teil der Gruppe {gruppe}."
    else:
        return False, f"Gruppe {gruppe} existiert nicht."


def remove_self(gruppe, spieler):
    if gruppen.get(gruppe):
        if spieler in gruppen[gruppe]["spieler"]:
            gruppen[gruppe]["spieler"].remove(spieler)
            return True, f"Du wurdest aus Gruppe {gruppe} entfernt."
        else:
            return False, f"Du bist kein Spieler der Gruppe {gruppe}."
    else:
        return False, f"Gruppe {gruppe} existiert nicht."
