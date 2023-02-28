from database import Database
from id_tools import *
from json_interface import *

# db = Database('')
# db.setup()

template = {'a': [{'x': 1}], 'b': {'c': 1, 'd': 1}}

x = JSONDict('test', template, {'a': [{'x': 1}, {'x': 2}]})
y = x._copy()
y.a[1].x = 10
print(x)
print(y)
delta = calculate_delta(x, y)
print(delta)
print(add_delta(x, delta))