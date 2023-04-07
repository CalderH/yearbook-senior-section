import json
import os.path
from enum import Enum
from typing import Tuple, List


class PathSource(Enum):
    core = c = 0
    school = s = 1
    year = y = 2
PS = PathSource


if os.path.exists('folders.json'):
    with open('folders.json') as file:
        _paths = json.load(file)

    _core_path_head = _paths['core']
    _school_path_head = _paths['school']
    _year_path_head = _paths['year']

    with open(os.path.join(_core_path_head, 'paths.json')) as file:
        core_paths = json.load(file)

    with open(os.path.join(_school_path_head, 'paths.json')) as file:
        school_paths = json.load(file)

    with open(os.path.join(_year_path_head, 'paths.json')) as file:
        year_paths = json.load(file)
    
    def construct_path(*args: List[PathSource | Tuple[PathSource, str] | str]) -> str:
        head_dict = {PS.core: _core_path_head, PS.school: _school_path_head, PS.year: _year_path_head}
        key_dict = {PS.core: core_paths, PS.school: school_paths, PS.year: year_paths}

        path_items = []
        for item in args:
            if isinstance(item, PathSource):
                path_items.append(head_dict[item])
            elif isinstance(item, str):
                path_items.append(item)
            elif isinstance(item, tuple):
                source, key = item
                path_items.append(key_dict[source][key])
            else:
                raise Exception('invalid input to construct_path')
        
        return os.path.join(*path_items)

    def core_path(key: str) -> str:
        return construct_path(PS.core, (PS.core, key))
    
    def school_path(key: str) -> str:
        return construct_path(PS.school, (PS.school, key))
    
    def year_path(key: str) -> str:
        return construct_path(PS.year, (PS.year, key))
else:
    with open('paths.json') as file:
        core_paths = json.load(file)
    
    def core_path(key, *args):
        return os.path.join(core_paths[key], *args)

    def construct_path(*_):
        raise NameError('construct_path is not defined when running from yearbook_core, since only core path is specified')
    
    def school_path(_):
        raise NameError('school_path is not defined when running from yearbook_core, since no school path is specified')

    def year_path(_):
        raise NameError('year_path is not defined when running from yearbook_core, since no year path is specified')

__all__ = ['construct_path', 'core_path', 'school_path', 'year_path', 'PathSource', 'PS']
