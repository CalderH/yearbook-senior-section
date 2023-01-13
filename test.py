from settings import *
from json_interface import *

student_template = {'a': [1]}
data = {'a': None}

# o = JSONDict('person', student_template, data)
# o.a = [True]
# print(o.a)

class Something(str):
    def __init__(self, string, char):
        super().__init__(string)
        # self.char = char

    def __hash__(self) -> int:
        if self[-1] == self.char:
            return hash(self[:-1])
        else:
            return super().__hash__()

x = Something('blah', '.')
y = Something('blah.', '.')
print(hash(x))
print(hash(y))