# This init file makes it possible to directly import config 
# as a package from everywhere in the project. 
# Messages and settings can be loaded from yaml files using the load function.
# This needs to be done before messages and settings are accessed.
# from config import messages, settings, constants

import yaml
from pathlib import Path
import argparse
import logging
from shutil import copyfile


# frequently used directories
ROOT = Path(__file__).absolute().parent.parent
RESOURCES = ROOT / "resources"
DATA = ROOT / "data"
CONFIG = ROOT / "config"
# other 'global' constants

# parse args and load config
parser = argparse.ArgumentParser(description="Run the Ilaris Discord Bot")
parser.add_argument("--debug", 
    action="store_true", default=None, 
    help="Enable debug logging")
parser.add_argument("--token",
    default=None, help="Discord bot token")
parser.add_argument("--settings",
    help="Path to a settings file",
    default=CONFIG/"settings.yml")
args = vars(parser.parse_args())
logging.info("Config loading with arguments: %s", args)

# create initial settings automatically for first time users
config_file = args.get('settings', CONFIG/"settings.yml")
if not config_file.exists():
    ask = f"Settings file {config_file} does not exist. Do you want to create it? (y/n)"
    answer = input(ask)
    if answer.lower() != "y":
        print("Settings file not created. Exiting...")
        exit()
    copyfile(CONFIG/"settings.example.yml", config_file)
    token = args.get("token")
    if token in [None, "YOUR_BOT_TOKEN"]:
        token = input("Please enter your bot token: ")
        with open(config_file, 'r', encoding="utf-8") as f:
            settings = yaml.safe_load(f)
        settings["token"] = token
        with open(config_file, 'w', encoding="utf-8") as f:
            yaml.safe_dump(settings, f)
    
# load configuration files and messages based on args
with open(config_file, 'r', encoding="utf-8") as f:
    settings = yaml.safe_load(f)
    # overwrite settings with args
    args.pop('settings')
    settings.update({k: v for k, v in args.items() if v is not None})
with open(CONFIG/"commands.yml", 'r', encoding="utf-8") as f:
    commands = yaml.safe_load(f)
with open(CONFIG/'messages.yml', 'r', encoding="utf-8") as f:
    messages = yaml.safe_load(f)
if settings.get("language", "en") != 'en':
    lang_file = CONFIG/f'messages_{settings["language"]}.yml'
    with open(lang_file, 'r', encoding="utf-8") as f:
        messages.update(yaml.safe_load(f))