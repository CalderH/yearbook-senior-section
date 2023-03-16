from database import Database
from id_tools import *
from json_interface import *

# db = Database('')
# db.setup()

template = {'a': [{'b': 1}, {'c': True}]}

x = JSONDict('test', template, {'a': 1})
# a = x.a = {}
# print(type(x.a))
# print(type(a))