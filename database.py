import json
from json_interface import *


with open('database_template.json') as file:
    database_template = json.load(file)


class YearbookDatabase:
    def __init__(self, )