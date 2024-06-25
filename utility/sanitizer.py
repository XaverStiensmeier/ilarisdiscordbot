import re


def sanitize(text):
    return re.sub(r'[^0-9a-zA-Z\-_]+', '', text.replace(" ", "-")).lower()
