from settings import *
from json_interface import *

student_template = {'a': 1}
data = {'a': None}

o = JSONDict('person', student_template, data, mark_edits=False)
o.a = 2
print(o)
