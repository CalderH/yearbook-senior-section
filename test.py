from database import Database
from id_tools import *
from json_interface import *

# db = Database('')
# db.setup()

template = {'a': None}

x = JSONDict('test', template, {'a': 2})
x.a = True
# a = x.a = {}
# print(type(x.a))
# print(type(a))