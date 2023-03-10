from database import Database
from id_tools import *
from json_interface import *

# db = Database('')
# db.setup()

template = {'a': {'b': 0}}

x = JSONDict('test', template, {})
a = x.a = {}
print(type(x.a))
print(type(a))