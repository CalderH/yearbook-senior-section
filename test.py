from json_interface import *

template = {'a': [1]}
value = {'a': [3]}

x = JSONDict('thing', template, value)
print(x)
