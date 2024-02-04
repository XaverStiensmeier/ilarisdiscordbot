import re


def sanitize_group_name(group_prefix, author):
    group_name = f"{group_prefix}_{author}"
    return re.sub('[^0-9a-zA-Z\-_]+', '', group_name.replace(" ", "-")).lower()


def sanitize_guild(guild):
    return re.sub('[^0-9a-zA-Z\-_]+', '', guild.name.replace(" ", "-")).lower()


def sanitize_prefix(prefix):
    return re.sub('[^0-9a-zA-Z\-_]+', '', prefix.replace(" ", "-")).lower()

