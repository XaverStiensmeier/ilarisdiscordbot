from pathlib import Path
import os
RESOURCES = os.path.join(Path(__file__).absolute().parent, "resources")


def rjoin(path):
    return os.path.join(RESOURCES, path)
