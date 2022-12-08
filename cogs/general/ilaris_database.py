#!/usr/bin/env python3

import yaml

import basic_paths
import cogs.general.differ

with open(basic_paths.rjoin("datenbank/discord.yml")) as file:
    flat_database = yaml.safe_load(file)


def get_database_entry(name):
    result = None
    result_str = ""
    result_name, three_best = cogs.general.differ.closest_match(name, flat_database.keys())
    if result_name:
        result = flat_database[result_name]
        if three_best:
            result_str += f"Die drei besten Matches sind: {three_best}\n\n"
    else:
        return f"{name} nicht gefunden..."

    result_str += f"**--- {name} ---**\n"
    # Prepare print
    for key, value in result.items():
        if value == 0 or value:
            result_str += f"**{key.title()}**:"
            if isinstance(value, list):
                result_str += "\n"
                for elem in value:
                    result_str += f"\t- {elem}\n"
            else:
                result_str += f" {value}\n"
    return result_str
