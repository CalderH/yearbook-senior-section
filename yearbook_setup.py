import json
import os.path


with open('paths.json') as file:
    _paths = json.load(file)

_core_path_head = _paths['core']
_school_path_head = _paths['school']
_year_path_head = _paths['year settings']

with open(os.path.join(_core_path_head, 'settings.json')) as file:
    core_settings = json.load(file)

with open(os.path.join(_school_path_head, 'settings.json')) as file:
    school_settings = json.load(file)

with open(os.path.join(_year_path_head, 'settings.json')) as file:
    year_settings = json.load(file)

def core_path(key, *args):
    return os.path.join(_core_path_head, core_settings[key], *args)

def school_path(key, *args):
    return os.path.join(_school_path_head, school_settings[key], *args)

def year_path(key, *args):
    return os.path.join(_year_path_head, year_settings[key], *args)
