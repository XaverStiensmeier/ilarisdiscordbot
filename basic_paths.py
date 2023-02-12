import os
from pathlib import Path

ROOT = Path(__file__).absolute().parent
RESOURCES = os.path.join(ROOT, "resources")


def rjoin(path):
    return os.path.join(RESOURCES, path)
