from settings import *


_edit_marker_char = '.'
_untracked_marker_char = '*'

def _create_marker_dict_functions(marker_char):
    def has_marker(name):
        return len(name) > 0 and name[-1] == marker_char

    def remove_marker(name):
        if has_marker(name):
            return name[:-1]
        else:
            return name

    def add_marker(name):
        if has_marker(name):
            return name
        else:
            return name + marker_char

    def in_dict(marker_dict, name):
        return remove_marker(name) in marker_dict or add_marker(name) in marker_dict

    def dict_get(marker_dict, name):
        name_with_marker = add_marker(name)
        name_without_marker = remove_marker(name)
        if name_without_marker in marker_dict:
            return marker_dict[name_without_marker]
        elif name_with_marker in marker_dict:
            return marker_dict[name_with_marker]
        else:
            raise KeyError(name)
    
    return has_marker, add_marker, remove_marker, in_dict, dict_get

_has_edit_marker, _add_edit_marker, _remove_edit_marker, _in_dict_edit, _dict_get_edit = _create_marker_dict_functions(_edit_marker_char)
_has_untracked_marker, _add_untracked_marker, _remove_untracked_marker, _in_dict_untracked, _dict_get_untracked = _create_marker_dict_functions(_untracked_marker_char)


def _check_types(name, value, template):
        if template is None:
            return
        type_names = {int: 'number', float: 'number', bool: 'boolean', str: 'string', list: 'list', dict: 'dict'}
        value_type_name = type_names[type(value)]
        template_type_name = type_names[type(template)]
        if value_type_name != template_type_name:
            raise TypeError(f'{name} must be a {template_type_name}; cannot be {value}')


class JSONDict:
    def __init__(self, type_name, template, data):
        self.__dict__['_type_name'] = type_name
        self.__dict__['_template'] = template
        self.__dict__['_data'] = data

    def _check_name(self, name):
        if self._template is not None and not _in_dict_untracked(self._template, name):
            raise AttributeError(f"{self._type_name} does not have the attribute \"{name}\"")
    
    def __getattr__(self, name):
        name = name.replace('_', ' ')
        self._check_name(name)
        
        if _in_dict_edit(self._data, name):
            data_value = _dict_get_edit(self._data, name)
            if self._template is None:
                template_value = None
            else:
                template_value = _dict_get_untracked(self._template, name)
            _check_types(f'{self._type_name}.{name}', data_value, template_value)
            if isinstance(template_value, dict) or (self._template is None and isinstance(data_value, dict)):
                return JSONDict(f'{self._type_name}.{name}', template_value, data_value)
            elif isinstance(template_value, list) or (self._template is None and isinstance(data_value, list)):
                if template_value is None or template_value == []:
                    item_template = None
                else:
                    item_template = template_value[0]
                return JSONList(f'{self._type_name}.{name}', item_template, data_value, self, name)
            else:
                return data_value
        else:
            return None
    
    def __setattr__(self, name, value):
        name = name.replace('_', ' ')
        self._check_name(name)
        if self._template is not None:
            _check_types(f'{self._type_name}.{name}', value, _dict_get_untracked(self._template, name))

        name_with_marker = _add_edit_marker(name)
        name_without_marker = _remove_edit_marker(name)
        if name_with_marker in self._data:
            assert name_without_marker not in self._data
            if self._data[name_with_marker] == value:
                return
            del self._data[name_with_marker]
        elif name_without_marker in self._data:
            if self._data[name_without_marker] == value:
                return
            del self._data[name_without_marker]
        
        if _remove_untracked_marker(name) in self._template:
            self._data[_add_edit_marker(name)] = value
        else:
            assert _add_untracked_marker(name) in self._template
            self._data[name] = value
    
    def __delattr__(self, name):
        name = name.replace('_', ' ')
        self._check_name(name)
        
        name_with_marker = _add_edit_marker(name)
        name_without_marker = _remove_edit_marker(name)
        if name_with_marker in self._data:
            assert name_without_marker not in self._data
            self._data[name_with_marker] = None
        elif name_without_marker in self._data:
            self._data[name_without_marker] = None

    def __str__(self):
        return str(self._data)


class JSONList:
    def __init__(self, type_name, item_template, data, edit_marker_obj, edit_marker_key):
        self._type_name = type_name
        self._item_template = item_template
        self._data = data
        self._edit_marker_obj = edit_marker_obj
        self._edit_marker_key = edit_marker_key
    
    def __getitem__(self, index):
        item = self._data[index]
        name = f'(item of {self._type_name})'
        _check_types(name, item, self._item_template)
        if isinstance(self._item_template, dict) or (self._item_template is None and isinstance(item, dict)):
            return JSONDict(name, self._item_template, item)
        elif isinstance(self._item_template, list) or (self._item_template is None and isinstance(item, list)):
            if self._item_template is None or self._item_template == []:
                item_template = None
            else:
                item_template = self._item_template[0]
            return JSONList(name, item_template, item, self._edit_marker_obj, self._edit_marker_key)
        else:
            return item

    def _handle_edit_marker(self):
        key_with_marker = _add_edit_marker(self._edit_marker_key)
        if key_with_marker in self._edit_marker_obj._data:
            return
        assert self._edit_marker_key in self._edit_marker_obj._data
        self._edit_marker_obj._data[key_with_marker] = self._edit_marker_obj._data[self._edit_marker_key]
        del self._edit_marker_obj._data[self._edit_marker_key]
    
    def __setitem__(self, index, value):
        current_value = self._data[index]
        if current_value == value:
            return
        _check_types(f'(item of {self._type_name})', value, self._item_template)
        self._data[index] = value
        self._handle_edit_marker()
    
    def __delitem__(self, index):
        del self._data[index]
        self._handle_edit_marker()
    
    def append(self, value):
        _check_types(f'(item of {self._type_name})', value, self._item_template)
        self._data.append(value)
        self._handle_edit_marker()
    
    def __str__(self):
        return str(self._data)


with open('template.json') as file:
    template = json.load(file)


def record(data):
    return JSONDict('person', template, data)
