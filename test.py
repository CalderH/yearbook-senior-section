from database import Database
from id_tools import *
from json_interface import *

# db = Database('')
# db.setup()

template = {'a': [[1, 2, 3]]}

x = JSONDict('test', template, {'a': [1, 2, 3, 4]})
# a = x.a = {}
# print(type(x.a))
# print(type(a))