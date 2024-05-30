# This init file makes it possible to directly import config 
# as a package from everywhere in the project. 
# Messages, settings and constants are loaded
# automatically at first import (before the bot starts) 
# and can be used via the config package:
# from config import messages, settings, constants

import yaml
from pathlib import Path

# load constants
from config import constants

# load settings
with open(Path("config")/"settings.yml", 'r', encoding="utf-8") as f:
    settings = yaml.safe_load(f)

# load commands
with open(Path("config")/"commands.yml", 'r', encoding="utf-8") as f:
    commands = yaml.safe_load(f)

# load messages and update language (from config import messages)
with open(Path("config")/'messages.yml', 'r', encoding="utf-8") as f:
    messages = yaml.safe_load(f)
if settings.get("language", "en") != 'en':
    lang_file = Path("config")/f'messages_{settings["language"]}.yml'
    with open(lang_file, 'r', encoding="utf-8") as f:
        messages.update(yaml.safe_load(f))