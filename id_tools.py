from enum import Enum
from typing import Tuple, Optional, NewType

initial_consonants = 'bcdfghjklmnprstvwyz'
consonants = 'bcdfghjklmnprstvwxyz'
vowels = 'aeiou'

start_id = 'ba'

ID = NewType('ID', str)

def next_id(id: str) -> str:
    """Given an ID, generates the next ID in the sequence of IDs"""

    id_letters, id_type = decompose_id(id)
    new_id = list(id_letters)
    for i in range(len(new_id) - 1, -1, -1):
        char = new_id[i]
        if i == 0:
            choices = initial_consonants
        elif i % 2 == 0:
            choices = consonants
        else:
            choices = vowels
        char_index = choices.index(char)
        if char_index == len(choices) - 1:
            new_id[i] = choices[0]
            if i == 0:
                if len(new_id) % 2 == 0:
                    new_id.append(consonants[0])
                else:
                    new_id.append(vowels[0])
        else:
            new_id[i] = choices[char_index + 1]
            break
    return convert_id(''.join(new_id), id_type)

class IDType(Enum):
    """The different things that an ID can be used for"""
    record = r = 0
    version = v = 1
    branch = b = 2
    view = w = 3

id_to_letter = {IDType.r: 'r', IDType.v: 'v', IDType.b: 'b', IDType.w: 'w'}
letter_to_id = {letter: id for id, letter in id_to_letter.items()}

separator = ','

def convert_id(id, *args):
    """Converts between IDs with prefixes and IDs without prefixes.

    If you input just an ID, or an ID and None, it will output the ID without the prefix.
    If you input a prefix-less ID and a prefix, it will combine them (with a separator in between).
    """
    if len(args) == 0 or args[0] is None:
        # Assumes that the prefix is one character long
        if len(id) >= 2 and id[1] == separator:
            return id[2:]
        else:
            return id
    else:
        return id_to_letter[args[0]] + separator + id
    
def decompose_id(id: str) -> Tuple[str, Optional[IDType]]:
    """Separates the prefix and suffix of an ID.

    Returns a tuple contianing the suffix (the unique sequence of letters),
    followed by the ID object representing the type of the ID (or none if the ID had no prefix)
    """
    if len(id) >= 2 and id[1] == separator:
        return id[2:], letter_to_id[id[0]]
    else:
        return id, None

def id_type(id: str) -> Optional[IDType]:
    return decompose_id(id)[1]

__all__ = ['start_id', 'next_id', 'IDType', 'convert_id', 'decompose_id', 'id_type', 'ID']