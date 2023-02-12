#!/usr/bin/env python3
import difflib


def closest_match(name, name_list):
    three_best = None
    if name in name_list:
        return name, None
    else:
        short_names = [key[:len(name)] for key in name_list]
        three_best = get_close_matches(name, short_names)
        if three_best:
            three_best = [list(name_list)[index] for index, best in three_best]
            name = three_best[0]
            return name, three_best
    return None, None


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
        if s.real_quick_ratio() >= cutoff and s.quick_ratio() >= cutoff and s.ratio() >= cutoff:
            result.append((s.ratio(), index, x))

    # Move the best scorers to head of list
    result.sort(reverse=True)
    # Strip scores for the best n matches
    return [(index, x) for score, index, x in result][:n]
