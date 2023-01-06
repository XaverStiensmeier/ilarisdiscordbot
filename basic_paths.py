from pathlib import Path
import os

ROOT = Path(__file__).absolute().parent
RESOURCES = os.path.join(ROOT, "resources")


def rjoin(path):
    return os.path.join(RESOURCES, path)
