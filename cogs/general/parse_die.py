#!/usr/bin/env python3
import random
import re

def roll_die(dice_number, sides, at=None):
    """
    at=0 don't at. at=1 smallest, at=n largest
    """
    summation = 0
    throws = []
    for elem in range(dice_number):
        current = random.randint(1, sides)
        throws.append(current)
        if not at:
            summation += current
    throws.sort(reverse=True)
    if at:
        return throws, throws[max(0, min(len(throws), at)) - 1]
    else:
        return throws, summation


def parse_single_value(text):
    if not "d" in text:
        return text, int(text)
    else:
        if "@" in text:
            at, dice_roll = text.split("@")
            dice_number, sides = re.split("d", dice_roll.lower())
            throws, result = roll_die(dice_number=int(dice_number), sides=int(sides), at=int(at))
            throws_str = [f"__**{d}**__" if a==int(at)-1 else f"{d}" for a, d in enumerate(throws)]
            at_str = f"[{', '.join(throws_str)}]"
            # return f"{result}({at}@{throws})", result
            return at_str, result
        else:
            dice_number, sides = re.split("d", text.lower())
            throws, result = roll_die(dice_number=int(dice_number), sides=int(sides))
            # return f"{result}({throws})", result
            return "[" + "+".join([f'**{d}**' for d in throws]) + "]", result


def parse_roll(text):
    text = text.lower().replace("w", "d")
    total_result = 0
    total_result_str = ""
    addends = text.split("+")
    img = None
    for addend in addends:
        subtraction = addend.split("-")
        result_str, result = parse_single_value(subtraction[0])
        total_result += result
        if "d20" in addend:
            img = result 
        if total_result_str != "":
            total_result_str += "+"  # only add + if there is a previous result
        total_result_str += f"{result_str}"
        for abstrahend in subtraction[1:]:
            result_str, result = parse_single_value(abstrahend)
            total_result -= result
            total_result_str += f"-{result_str}"
    return total_result_str, total_result, img
