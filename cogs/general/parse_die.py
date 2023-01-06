#!/usr/bin/env python3
import random
import re


def roll_die(n, at, sides, modification):
    """
    at=0 don't at. at=1 smallest, at=n largest
    """
    summation = modification
    throws = []
    for elem in range(int(n)):
        current = random.randint(1, int(sides))
        throws.append(current)
        summation += current
    if at:
        throws.sort(reverse=True)
        return throws[at - 1]
    else:
        return summation


def parse_die(text):
    modification = 0
    arguments = text.split("@")
    if len(arguments) == 2:
        at = int(arguments[0])
        text = arguments[1]
    else:
        at = 0
    arguments = text.split("-")
    if len(arguments) >= 2:
        for elem in arguments[1:]:
            modification -= int(elem)
        text = arguments[0]
    else:
        arguments = text.split("+")
        if len(arguments) >= 2:
            for elem in arguments[1:]:
                modification += int(elem)
            text = arguments[0]
    if text[0].isdigit():
        values = re.split("d|w",text.lower())
        return roll_die(values[0], at, values[1], modification)
