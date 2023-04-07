from enum import Enum
from typing import Tuple, Optional, NewType
import re

initial_consonants = 'bcdfghjklmnprstvwyz'
consonants = 'bcdfghjklmnprstvwxyz'
vowels = 'aeiou'

class IDType(Enum):
    """The different things that an ID can be used for"""
    record = r = 0
    version = v = 1
    branch = b = 2
    view = w = 3

id_to_letter = {IDType.r: 'r', IDType.v: 'v', IDType.b: 'b', IDType.w: 'w'}
letter_to_id = {letter: id for id, letter in id_to_letter.items()}

separator = ','

id_regex = '^([' + ''.join(id_to_letter.values()) + ']?)' + separator + '([' + vowels + ']|\d+|)([' + initial_consonants + '][' + vowels + '](?:[' + consonants + '][' + vowels + '])*[' + consonants + ']?)$'

start_sequence = 'ba'

ID = NewType('ID', str)

def next_id(id: str) -> str:
    """Given an ID, generates the next ID in the sequence of IDs"""

    id_type, user, sequence = decompose_id(id)
    new_sequence = list(sequence)
    for i in range(len(new_sequence) - 1, -1, -1):
        char = new_sequence[i]
        if i == 0:
            choices = initial_consonants
        elif i % 2 == 0:
            choices = consonants
        else:
            choices = vowels
        char_index = choices.index(char)
        if char_index == len(choices) - 1:
            new_sequence[i] = choices[0]
            if i == 0:
                if len(new_sequence) % 2 == 0:
                    new_sequence.append(consonants[0])
                else:
                    new_sequence.append(vowels[0])
        else:
            new_sequence[i] = choices[char_index + 1]
            break
    
    return compose_id(id_type, user, ''.join(new_sequence))

def compose_id(id_type: IDType, user: str, sequence: str):
    """Creates an ID out of the parts."""

    if id_type is None:
        type_str = ''
    else:
        type_str = id_to_letter[id_type]
    return type_str + separator + user + sequence

root_version_id = compose_id(IDType.version, '', 'ROOT')
trunk_branch_id = compose_id(IDType.branch, '', 'TRUNK')
    
def decompose_id(id: str) -> Tuple[IDType, str, str]:
    """Separates the type, user, and sequence of an ID.

    Returns a tuple containing
    - an ID object representing the type of the ID (or none if the ID had no prefix)
    - a string representing the user who created this id (can be empty)
    - sequence (the unique pronounceable sequence of letters)
    """

    if id == root_version_id:
        return IDType.version, '', 'ROOT'
    elif id == trunk_branch_id:
        return IDType.branch, '', 'TRUNK'

    match = re.findall(id_regex, id)
    if len(match) == 0:
        raise Exception(f'{id} is not a valid id')
    else:
        id_type, user, sequence = match[0]
        if id_type == '':
            id_type = None
        else:
            id_type = letter_to_id[id_type]
        return id_type, user, sequence


def id_type(id: str) -> Optional[IDType]:
    return decompose_id(id)[0]
