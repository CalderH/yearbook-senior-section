# from database import Database
from id_tools import *
from json_interface import *


template = {'b': 1, 'a': True}
x = JSONList('thing', template, [{'a': False, 'b': 1}])
print(x._data)
x.print()

# TODO test creating revisions on each input to a merge