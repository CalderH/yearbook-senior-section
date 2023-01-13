from settings import *
from json_interface import *

student_template = {'': 1}
data = {'a': 'hi'}

o = JSONDict('person', student_template, data)
print(o)
