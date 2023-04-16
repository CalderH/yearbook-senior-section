# from database import Database
from ids import *
from json_interface import *

from abc import ABC, abstractmethod

class A(ABC):
    def __init__(self):
        super().__init__()
        self.a = 1
    
class B(ABC):
    def __init__(self):
        super().__init__()
        self.b = 2

class C(A, B):
    def test(self):
        print(self.a, self.b)
    # def __init__(self):
    #     super().__init__()
    #     print('c')

c = C()
c.test()
# a['hi'] = 1
# a.print()

# x = JSONDict('a', {}, {})
# print(x.__dict__)



# TODO test creating revisions on each input to a merge