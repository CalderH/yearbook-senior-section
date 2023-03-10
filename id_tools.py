from enum import Enum

initial_consonants = 'bcdfghjklmnprstvwyz'
consonants = 'bcdfghjklmnprstvwxyz'
vowels = 'aeiou'

start_id = 'ba'

def next_id(id):
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

class ID(Enum):
    record = 0
    r = 0
    version = 1
    v = 1
    branch = 2
    b = 2
    view = 3
    w = 3

id_to_letter = {ID.r: 'r', ID.v: 'v', ID.b: 'b', ID.w: 'w'}
letter_to_id = {letter: id for id, letter in id_to_letter.items()}

separator = ','

def convert_id(id, *args):
    if len(args) == 0 or args[0] is None:
        if len(id) >= 2 and id[1] == separator:
            print(id)
            return id[2:]
        else:
            return id
    else:
        return id_to_letter[args[0]] + separator + id
    
def decompose_id(id):
    if len(id) >= 2 and id[1] == separator:
        return id[2:], letter_to_id[id[0]]
    else:
        return id, None

__all__ = ['start_id', 'next_id', 'ID', 'convert_id', 'decompose_id']