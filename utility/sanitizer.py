import re


def sanitize(text):
    return re.sub(r'[^0-9a-zA-Z\-_]+', '', text.replace(" ", "-")).lower()


def cap(s, l=1024):
    """Convert not existing to empty string and cut total string length.
    Discord has char limits for messages and other elements. Message fails if too long.
    """
    if not s:
        return "" 
    s = str(s)
    if len(s) > l:
        return s[:(l-4)] + "..."
    return s