from pathlib import Path
import os
RESOURCES = Path(__file__).absolute().parents[2]


def rjoin(path):
    return os.path.join(RESOURCES, path)
