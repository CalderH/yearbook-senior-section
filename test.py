# import interface
import json_interface

jf = json_interface.JSONFile('jf_test.json', 'thing', {'a': 1, 'b': [1]})
jf.load()
print(jf.a)








# # from database import Database
# from ids import *
# from json_interface import *

# from abc import ABC, abstractmethod

# a = JSONDict('a', {'x': {'y': 1}}, {'x': {'y': 1}})
# x = a.x
# x.y = 2
# print(a)

# TODO test creating revisions on each input to a merge