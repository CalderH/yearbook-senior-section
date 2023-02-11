def underscores_to_spaces(name):
    return name.replace('_', ' ')


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
        self.__dict__['_any_keys'] = template is not None and template.keys() == {''}
        self.__dict__['_data'] = data

        self._type_check()
    
    def _element_type_name(self, name):
        if self._any_keys:
            return f'(element of {self._type_name})'
        else:
            return f'{self._type_name}.{name}'

    def _type_check(self):
        if self._template is None:
            return
        for name, data_value in self._data.items():
            self._check_name(name)
            if self._any_keys:
                template_value = self._template['']
            else:
                template_value = self._template[name]
            _shallow_type_check(self._element_type_name(name), data_value, template_value)
            if isinstance(template_value, list) or isinstance(template_value, dict):
                # Creates a JSONDict or JSONList, which type-check themselves in the __init__ function 
                self.__getattr__(name)

    def _check_name(self, name):
        if self._template is not None and not self._any_keys and name not in self._template:
            raise AttributeError(f'{self._type_name} has no attribute \'{name}\'')
    
    def __getattr__(self, name):
        name = underscores_to_spaces(name)
        self._check_name(name)
        
        if name in self._data:
            data_value = self._data.name
            if data_value is None:
                return None
            if self._template is None:
                template_value = None
            elif self._any_keys:
                template_value = self._template['']
            else:
                template_value = self._template[name]
            if isinstance(template_value, dict) or (template_value is None and isinstance(data_value, dict)):
                if template_value == {}:
                    template_value = None
                return JSONDict(self._element_type_name(name), template_value, data_value)
            elif isinstance(template_value, list) or (template_value is None and isinstance(data_value, list)):
                if template_value is None or template_value == []:
                    item_template = None
                else:
                    item_template = template_value[0] # TODO
                return JSONList(self._element_type_name(name), item_template, data_value)
            else:
                return data_value
        else:
            return None
    
    def __hasattr__(self, name):
        return name in self._data and self._data.name is not None
    
    def __setattr__(self, name, value):
        name = underscores_to_spaces(name)
        
        if self._template is not None:
            self._check_name(name)
            type_name = self._element_type_name(name)
            if self._any_keys:
                template_value = self._template['']
            else:
                template_value = self._template[name]
            _shallow_type_check(type_name, value, template_value)
            if isinstance(template_value, dict) and template_value != {}:
                JSONDict(type_name, template_value, value)
            if isinstance(template_value, list) and template_value != []: # TODO can it also be [None]?
                JSONList(type_name, template_value[0], value)
        
        self._data[name] = value
    
    def __delattr__(self, name):
        name = underscores_to_spaces(name)
        self._check_name(name)
        del self._data[name]
    
    def __getitem__(self, name):
        return self.__getattr__(name)
    
    def __contains__(self, name):
        return self.__hasattr__(self, name)
    
    def __setitem__(self, name, value):
        self.__setattr__(name, value)
    
    def __delitem__(self, name):
        self.__delattr__(name)

    def __repr__(self):
        return f'{self._type_name}: {self._data}'
    
    def __str__(self):
        return self.__repr__()


class JSONList:
    def __init__(self, type_name, item_template, data):
        self._type_name = type_name
        self._item_template = item_template
        self._data = data
        self._item_type_name = f'(item of {self._type_name})'

        self._type_check()
    
    def _type_check(self):
        if self._item_template is None:
            return
        for index in range(len(self._data)):
            item = self._data[index]
            _shallow_type_check(self._item_type_name, item, self._item_template)
            if isinstance(self._item_template, list) or isinstance(self._item_template, dict):
                self.__getitem__(index)._type_check()
    
    def __getitem__(self, index):
        item = self._data[index]
        name = self._item_type_name
        if isinstance(self._item_template, dict) or (self._item_template is None and isinstance(item, dict)):
            dict_template = self._item_template
            if dict_template == {}:
                dict_template = None
            return JSONDict(name, dict_template, item, mark_edits=self._mark_edits)
        elif isinstance(self._item_template, list) or (self._item_template is None and isinstance(item, list)):
            if self._item_template is None or self._item_template == []:
                item_template = None
            else:
                item_template = self._item_template[0]
            return JSONList(name, item_template, item)
        else:
            return item
    
    def _recursive_check_types(self, value):
        _shallow_type_check(self._item_type_name, value, self._item_template)
        if isinstance(self._item_template, dict) and self._item_template != {}:
            JSONDict(self._item_type_name, self._item_template, value)
        if isinstance(self._item_template, list) and self._item_template != []:
            JSONList(self._item_type_name, self._item_template[0], value)
    
    def __setitem__(self, index, value):
        current_value = self._data[index]
        self._recursive_check_types(value)
        self._data[index] = value
    
    def __delitem__(self, index):
        del self._data[index]
    
    def append(self, value):
        self._recursive_check_types(value)
        self._data.append(value)
    
    def __repr__(self):
        return f'{self._type_name}: {self._data}'
    
    def __str__(self):
        return self.__repr__()
