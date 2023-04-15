# from database import Database
from ids import *
from json_interface import *

from abc import ABC, abstractmethod

class A(ABC):
    def __init__(self, x):
        self.x = x
    
    def print_x(self):
        print(self.x)

class B(A, JSONDict):
    def __init__(self, x):
        
        JSONDict.__init__(self, 'a', {'x': 1}, {})
        A.__init__(self, x)
        print(super(JSONDict, self).__dict__)

a = B(5)
# a['hi'] = 1
# a.print()

# x = JSONDict('a', {}, {})
# print(x.__dict__)



# TODO test creating revisions on each input to a merge