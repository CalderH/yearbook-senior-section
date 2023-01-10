import json


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


class JSONInterface:
    def __init__(self, type_name, template, data):
        self.__dict__['_type_name'] = type_name
        self.__dict__['_template'] = template
        self.__dict__['_data'] = data
    
    def __getattr__(self, __name):
        __name = __name.replace('_', ' ')
        if not _in_dict_untracked(self._template, __name):
            raise AttributeError(f"{self._type_name} does not have the attribute \"{__name}\"")
        
        if _in_dict_edit(self._data, __name):
            data_value = _dict_get_edit(self._data, __name)
            template_value = _dict_get_untracked(self._template, __name)
            if isinstance(template_value, dict):
                return JSONInterface(__name, template_value, data_value)
            else:
                return data_value
        else:
            return None
    
    def __setattr__(self, __name, __value):
        # TODO: type check
        __name = __name.replace('_', ' ')
        if not _in_dict_untracked(self._template, __name):
            raise AttributeError(f"{self._type_name} does not have the attribute \"{__name}\"")

        name_with_marker = _add_edit_marker(__name)
        name_without_marker = _remove_edit_marker(__name)
        if name_with_marker in self._data:
            assert name_without_marker not in self._data
            if self._data[name_with_marker] == __value:
                return
            del self._data[name_with_marker]
        elif name_without_marker in self._data:
            if self._data[name_without_marker] == __value:
                return
            del self._data[name_without_marker]
        
        if _remove_untracked_marker(__name) in self._template:
            self._data[_add_edit_marker(__name)] = __value
        else:
            assert _add_untracked_marker(__name) in self._template
            self._data[__name] = __value
    
    def __delattr__(self, __name):
        __name = __name.replace('_', ' ')
        if not _in_dict_untracked(self._template, __name):
            raise AttributeError(f"{self._type_name} does not have the attribute \"{__name}\"")
        
        name_with_marker = _add_edit_marker(__name)
        name_without_marker = _remove_edit_marker(__name)
        if name_with_marker in self._data:
            assert name_without_marker not in self._data
            self._data[name_with_marker] = None
        elif name_without_marker in self._data:
            self._data[name_without_marker] = None

    def __repr__(self):
        return str(self._data)


with open('template.json') as file:
    template = json.load(file)


def record(data):
    return JSONInterface('person', template, data)
