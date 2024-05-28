import os
from pathlib import Path

ROOT = Path(__file__).absolute().parent
RESOURCES = os.path.join(ROOT, "resources")
DATA = os.path.join(ROOT, "data")


def rjoin(path):
    return os.path.join(RESOURCES, path)


def djoin(path):
    return os.path.join(DATA, path)