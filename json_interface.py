# _edit_marker_char = '.'
# _untracked_marker_char = '*'

# def _create_marker_dict_functions(marker_char):
#     def has_marker(name):
#         return len(name) > 0 and name[-1] == marker_char

#     def remove_marker(name):
#         if has_marker(name):
#             return name[:-1]
#         else:
#             return name

#     def add_marker(name):
#         if has_marker(name):
#             return name
#         else:
#             return name + marker_char

#     def in_dict(marker_dict, name):
#         return remove_marker(name) in marker_dict or add_marker(name) in marker_dict

#     def dict_get(marker_dict, name):
#         name_with_marker = add_marker(name)
#         name_without_marker = remove_marker(name)
#         if name_without_marker in marker_dict:
#             return marker_dict[name_without_marker]
#         elif name_with_marker in marker_dict:
#             return marker_dict[name_with_marker]
#         else:
#             raise KeyError(name)
    
#     return has_marker, add_marker, remove_marker, in_dict, dict_get

# _has_edit_marker, _add_edit_marker, _remove_edit_marker, _in_dict_edit, _dict_get_edit = _create_marker_dict_functions(_edit_marker_char)
# _has_untracked_marker, _add_untracked_marker, _remove_untracked_marker, _in_dict_untracked, _dict_get_untracked = _create_marker_dict_functions(_untracked_marker_char)


class EditDict(dict):
    _original = 0
    _edited = 1
    _deleted = 2

    _edit_marker_char = '.'

    def __init__(self, input_dict):
        self._key_statuses = {}

        adjusted_dict = {}
        for key, value in input_dict.items():
            if value is None:
                self._key_statuses[key] = EditDict._deleted
            elif key != '' and key[-1] == EditDict._edit_marker_char:
                clean_key = key[:-1]
                adjusted_dict[clean_key] = value
                self._key_statuses[clean_key] = EditDict._edited
            else:
                adjusted_dict[key] = value
                self._key_statuses[key] = EditDict._original

        super().__init__(adjusted_dict)
    
    def __setitem__(self, key, value):
        if key not in self or self[key] != value:
            self._key_statuses[key] = EditDict._edited
        super().__setitem__(key, value)
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._key_statuses[key] = EditDict._deleted
    
    def mark_edited(self, key):
        self._key_statuses[key] = EditDict._edited

    def write(self):
        output = {}
        for key, status in self._key_statuses.items():
            if status == EditDict._original:
                output[key] = self[key]
            elif status == EditDict._edited:
                output[key + EditDict._edit_marker_char] = self[key]
            else:
                output[key] = None
        return output



def _shallow_type_check(name, value, template):
        if template is None or value is None:
            return
        type_names = {int: 'number', float: 'number', bool: 'boolean', str: 'string', list: 'list', dict: 'dict'}
        value_type_name = type_names[type(value)]
        template_type_name = type_names[type(template)]
        if value_type_name != template_type_name:
            raise TypeError(f'{name} must be a {template_type_name}; it cannot be {repr(value)}')


class JSONDict:
    def __init__(self, type_name, template, data):
        self.__dict__['_type_name'] = type_name
        self.__dict__['_template'] = template
        self.__dict__['_data'] = data

        self._type_check()

    def _type_check(self):
        if self._template is None:
            return
        for name, data_value in self._data.items():
            self._check_name(name)
            template_value = self._template[name]
            _shallow_type_check(f'{self._type_name}.{name}', data_value, template_value)
            if isinstance(template_value, list) or isinstance(template_value, dict):
                self.__getattr__(name)

    def _check_name(self, name):
        if self._template is not None and name not in self._template:
            raise AttributeError(f'{self._type_name} has no attribute \'{name}\'')
    
    def __getattr__(self, name):
        name = name.replace('_', ' ')
        self._check_name(name)
        
        if name in self._data:
            data_value = self._data[name]
            if data_value is None:
                return None
            if self._template is None:
                template_value = None
            else:
                template_value = self._template[name]
            if isinstance(template_value, dict) or (template_value is None and isinstance(data_value, dict)):
                if template_value == {}:
                    template_value = None
                return JSONDict(f'{self._type_name}.{name}', template_value, data_value)
            elif isinstance(template_value, list) or (template_value is None and isinstance(data_value, list)):
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
        
        if self._template is not None:
            self._check_name(name)
            type_name = f'{self._type_name}.{name}'
            _shallow_type_check(type_name, value, _dict_get_untracked(self._template, name))
            template_value = _dict_get_untracked(self._template, name)
            if isinstance(template_value, dict) and template_value != {}:
                JSONDict(type_name, template_value, value)
            if isinstance(template_value, list) and template_value != []:
                JSONList(type_name, template_value[0], value, self, name)

        name_with_marker = _add_edit_marker(name)
        name_without_marker = _remove_edit_marker(name)
        if name_with_marker in self._data:
            assert name_without_marker not in self._data
            old_value = self._data[name_with_marker]
            if old_value == value and type(old_value) == type(value):
                return
            del self._data[name_with_marker]
        elif name_without_marker in self._data:
            old_value = self._data[name_without_marker]
            if old_value == value and type(old_value) == type(value):
                return
            del self._data[name_without_marker]
        
        if self._template is None or _remove_untracked_marker(name) in self._template:
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
        return f'{self._type_name}: {self._data}'


class JSONList:
    def __init__(self, type_name, item_template, data, edit_marker_obj, edit_marker_key):
        self._type_name = type_name
        self._item_template = item_template
        self._data = data
        self._edit_marker_obj = edit_marker_obj
        self._edit_marker_key = edit_marker_key

        self._type_check()
    
    def _type_check(self):
        if self._item_template is None:
            return
        for index in range(len(self._data)):
            item = self._data[index]
            _shallow_type_check(f'(item of {self._type_name})', item, self._item_template)
            if isinstance(self._item_template, list) or isinstance(self._item_template, dict):
                self.__getitem__(index)._type_check()
    
    def __getitem__(self, index):
        item = self._data[index]
        name = f'(item of {self._type_name})'
        if isinstance(self._item_template, dict) or (self._item_template is None and isinstance(item, dict)):
            dict_template = self._item_template
            if dict_template == {}:
                dict_template = None
            return JSONDict(name, dict_template, item)
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
    
    def _recursive_check_types(self, value):
        type_name = f'(item of {self._type_name})'
        _shallow_type_check(type_name, value, self._item_template)
        if isinstance(self._item_template, dict) and self._item_template != {}:
            JSONDict(type_name, self._item_template, value)
        if isinstance(self._item_template, list) and self._item_template != []:
            JSONList(type_name, self._item_template[0], value, self._edit_marker_obj, self._edit_marker_key)
    
    def __setitem__(self, index, value):
        current_value = self._data[index]
        if current_value == value and type(current_value) == type(value):
            return
        self._recursive_check_types(value)
        self._data[index] = value
        self._handle_edit_marker()
    
    def __delitem__(self, index):
        del self._data[index]
        self._handle_edit_marker()
    
    def append(self, value):
        self._recursive_check_types(value)
        self._data.append(value)
        self._handle_edit_marker()
    
    def __str__(self):
        return f'{self._type_name}: {self._data}'
