from pathlib import Path

# set to 'de' for German or add your own messages_<LANGUAGE>.yml file
LANGUAGE = 'en'

# frequently used directories
ROOT = Path(__file__).absolute().parent
RESOURCES = ROOT / "resources"
DATA = ROOT / "data"