from settings import *
from object_interface import *

template = {'list': []}
data = {'list': [0]}

o = JSONDict('person', template, data)

print(o.list)
o.list.append(True)
print(o.list)
