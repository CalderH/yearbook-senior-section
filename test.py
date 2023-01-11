from settings import *
from json_interface import *

template = {'a': [[[{'b': [1]}]]]}
data = {'a': []}

o = JSONDict('person', template, data)
o.a.append([[{'b': [1]}]])
print(o)