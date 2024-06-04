# This init file makes it possible to directly import config 
# as a package from everywhere in the project. 
# Messages and settings can be loaded from yaml files using the load function.
# This needs to be done before messages and settings are accessed.
# from config import messages, settings, constants

import yaml
from pathlib import Path

# frequently used directories
ROOT = Path(__file__).absolute().parent.parent
RESOURCES = ROOT / "resources"
DATA = ROOT / "data"
CONFIG = ROOT / "config"


# init module variables
settings = None
messages = None

# load module content from files
def load(cfg, args):
    with open(args.get('settings', CONFIG/"settings.yml"), 'r', encoding="utf-8") as f:
        cfg.settings = yaml.safe_load(f)
    # load commands
    with open(CONFIG/"commands.yml", 'r', encoding="utf-8") as f:
        cfg.commands = yaml.safe_load(f)
    # load messages and update language (from config import messages)
    with open(CONFIG/'messages.yml', 'r', encoding="utf-8") as f:
        cfg.messages = yaml.safe_load(f)
    if cfg.settings.get("language", "en") != 'en':
        lang_file = CONFIG/f'messages_{cfg.settings["language"]}.yml'
        with open(lang_file, 'r', encoding="utf-8") as f:
            cfg.messages.update(yaml.safe_load(f))