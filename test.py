from settings import *
from json_interface import *

student_template = {'a': [1]}
data = {'a': None}

# o = JSONDict('person', student_template, data)
# o.a = [True]
# print(o.a)




x = EditDict({'a': 0, 'b': {'c': 1}})
x['b']['c'] = 2
print(x.write())