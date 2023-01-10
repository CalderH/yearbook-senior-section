from settings import *

from object_interface import *

template = {'name': {'first': '', 'middle': '', 'last': ''}, 'age*': 10, 'notes*': []}
data = {'name': {'first': 'Calder', 'last': 'Hansen'}, 'age': 22, 'notes': ['hi']}


o = JSONInterface('person', template, data)

print(o)
del o.name.first
print(o)