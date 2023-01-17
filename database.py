import json
from json_interface import *
from yearbook_setup import core_path


with open(core_path('database template')) as file:
    database_template = json.load(file)


class Database:
    def __init__(self, path):
        with open(path) as file:
            self.obj = JSONDict(json.load(file))
    
    