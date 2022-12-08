#!/usr/bin/env python3
import difflib

import yaml

import basic_paths

with open(basic_paths.rjoin("datenbank/discord.yml")) as file:
    flat_database = yaml.safe_load(file)


def get_close_matches(word, possibilities, n=3, cutoff=0.6):
    """
    See difflib
    Use SequenceMatcher to return list of the best "good enough" matches.
    word is a sequence for which close matches are desired (typically a
    string).
    possibilities is a list of sequences against which to match word
    (typically a list of strings).
    Optional arg n (default 3) is the maximum number of close matches to
    return.  n must be > 0.
    Optional arg cutoff (default 0.6) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.
    The best (no more than n) matches among the possibilities are returned
    in a list, sorted by similarity score, most similar first.
    >>> get_close_matches("appel", ["ape", "apple", "peach", "puppy"])
    ['apple', 'ape']
    >>> import keyword as _keyword
    >>> get_close_matches("wheel", _keyword.kwlist)
    ['while']
    >>> get_close_matches("Apple", _keyword.kwlist)
    []
    >>> get_close_matches("accept", _keyword.kwlist)
    ['except']
    """
    if not n > 0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = difflib.SequenceMatcher()
    s.set_seq2(word)
    for index, x in enumerate(possibilities):
        s.set_seq1(x)
        if s.real_quick_ratio() >= cutoff and \
                s.quick_ratio() >= cutoff and \
                s.ratio() >= cutoff:
            result.append((s.ratio(), index, x))

    # Move the best scorers to head of list
    result.sort(reverse=True)
    # Strip scores for the best n matches
    return [(index, x) for score, index, x in result][:n]


def get_database_entry(name):
    result = None
    result_str = ""
    element_full_names = flat_database.keys()
    if name in element_full_names:
        result = flat_database[name]
    else:
        element_names = [key[:len(name)] for key in element_full_names]
        three_best = get_close_matches(name, element_names)
        if three_best:
            three_best = [list(element_full_names)[index] for index, best in three_best]
            name = three_best[0]
            result = flat_database[name]
            result_str += f"Die drei besten Matches: {three_best}\n\n"
    # key is the last key in the run and result is either None (if none found) or the right one
    if not result:
        return f"{name} nicht gefunden..."

    result_str += f"**--- {name} ---**\n"

    # Prepare print
    for key, value in result.items():
        if value == 0 or value:
            result_str += f"**{key.title()}**:"
            if isinstance(value, list):
                result_str += "\n"
                for elem in value:
                    result_str += f"\t- {elem}\n"
            else:
                result_str += f" {value}\n"
    return result_str
