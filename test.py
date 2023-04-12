# from database import Database
from ids import *
from json_interface import *

from abc import ABC, abstractmethod

class A(ABC):
    thing = ...

class B(A):
    thing = 5

a = B()
print(a.thing)



# TODO test creating revisions on each input to a merge