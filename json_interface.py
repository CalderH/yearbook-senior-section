from json import dumps
from copy import deepcopy
from typing import *


JSONValue = Union[None, int, float, bool, str, list, dict]


def underscores_to_spaces(name: str) -> str:
    return name.replace('_', ' ')

# Lists are used in templates to represent a few things
# A list template with zero items represents a list value with no type restrictions
# A list template with one item represents a list value, and the one item represents the type of all the elements
# A list template with more than one item represents a single value, and the multiple items represent multiple options for that value
#     If all the template values have the same type, then the value must equal one of the template values
#     If the template values have multiple types, then the value must have the same type as one of the template values
# 
# For example:
# [1]: a list where every item is a number
# [1, True]: a single value that is either a number or a boolean
# [1, 2]: a single value that is either 1 or 2
# [[1, True]]: a list of items that can be either numbers or booleans
# [[1, 2]]: a list of items that can only be 1 or 2

def _is_list(template: JSONValue) -> bool:
    """Returns whether this template represents a list."""

    return isinstance(template, list) and len(template) <= 1


def _is_choice(template: JSONValue) -> bool:
    """Returns whether this template represents multiple options for a single value."""

    return isinstance(template, list) and len(template) > 1


def _shallow_type_check(name: str, value: JSONValue, template: JSONValue):
    """"""

    # Null template matches everything
    # Everything matches null value
    if template is None or value is None:
        return
    
    # Dict of type names
    # Use for comparing types (since we're treating ints and floats as the same)
    # and for error messages
    type_names = {int: 'number', float: 'number', bool: 'boolean', str: 'string', list: 'list', dict: 'dict'}

    value_type_name = type_names[type(value)]

    # If the template represents multiple options for a single value
    if _is_choice(template):
        # Template is guaranteed to be a list now; tell that to the type checker
        template = cast(list, template)

        # Get the type name for everything in the template
        template_type_names: list[str] = [type_names[type(choice)] for choice in template]

        # If all the options in the template have the same type,
        # then just check whether the value is equal to one of those options
        if len(set(template_type_names)) == 1:
            if value not in template:
                raise TypeError(f'{name} must be one of {template}; it cannot be {repr(value)}')
            
        # Otherwise we need to check if the value matches the type and structure of one of those options
        else:
            # Check the value against each option one by one
            found_type = False
            for option in template:
                # Skip over ones with a different type
                option_type_name = type_names[type(option)]
                if option_type_name != value_type_name:
                    continue

                # At this point we have found something with the same top-level type
                found_type = True
                # But it might not have the same structure (e.g. list of numbers vs list of strings)
                if option_type_name == 'dict':
                    try:
                        # Creating a JSONDict will automatically check whether the structure is the same
                        JSONDict(name, option, value)
                        # If we get this far, then we have found an option that matches the value
                        return
                    except:
                        pass
                elif option_type_name == 'list':
                    # There is the possibility that the option may be itself a choice of options
                    # e.g. [[1, 2], 'a'] represents a value that can be 1, 2, or any string
                    if _is_choice(option):
                        try:
                            _shallow_type_check(name, value, option)
                            return
                        except:
                            pass
                    else:
                        try:
                            # creating a JSONList will automatically check whether the structure is the same
                            # have to take option[0] since JSONList inputs the type of an *item* of the list
                            JSONList(name, option[0], value)
                            return
                        except:
                            pass
                else:
                    return
            if found_type:
                raise TypeError(f'{name} must match one of {template}; it cannot be {repr(value)}')
            else:
                raise TypeError(f'{name} must be one of the types {template_type_names}; it cannot be {repr(value)}')
        
    else:
        template_type_name = type_names[type(template)]
        if value_type_name != template_type_name:
            raise TypeError(f'{name} must be a {template_type_name}; it cannot be {repr(value)}')


class JSONDict:
    def __init__(self, type_name: str, template: Optional[dict], data: JSONValue):
        self.__dict__['_type_name'] = type_name
        self.__dict__['_template'] = template
        self.__dict__['_any_keys'] = template is not None and template.keys() == {''}
        self.__dict__['_data'] = data

        self._type_check()
    
    def _element_type_name(self, name: str):
        if self._any_keys:
            return f'(element of {self._type_name})'
        else:
            return f'{self._type_name}.{name}'
        
    def _check_name(self, name):
        if self._template is not None and not self._any_keys and name not in self._template:
            raise AttributeError(f'{self._type_name} has no attribute \'{name}\'')

    def _type_check(self):
        if self._template is None:
            return
        if self._any_keys:
            template_value = self._template['']
        for name, data_value in self._data.items():
            self._check_name(name)
            if not self._any_keys:
                template_value = self._template[name]
            _shallow_type_check(self._element_type_name(name), data_value, template_value)
            if _is_list(template_value) or isinstance(template_value, dict):
                # Creates a JSONDict or JSONList, which type-check themselves in the __init__ function 
                self.__getattr__(name)
    
    def __getattr__(self, name):
        name = underscores_to_spaces(name)
        self._check_name(name)
        
        if name in self._data:
            data_value = self._data[name]
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
            elif _is_list(template_value) or (template_value is None and isinstance(data_value, list)):
                if template_value is None or template_value == []:
                    item_template = None
                else:
                    item_template = template_value[0]
                return JSONList(self._element_type_name(name), item_template, data_value)
            else:
                return data_value
        else:
            return None
    
    def __hasattr__(self, name):
        return name in self._data and self._data[name] is not None
    
    def __iter__(self):
        return {name: value for name, value in self._data if value is not None}
    
    def __setattr__(self, name, value):
        name = underscores_to_spaces(name)

        if isinstance(value, JSONDict) or isinstance(value, JSONList):
            value = value._data
        
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
            if _is_list(template_value) and template_value != []: # TODO can it also be [None]?
                JSONList(type_name, template_value[0], value)
        
        self._data[name] = value
    
    def __delattr__(self, name):
        name = underscores_to_spaces(name)
        self._check_name(name)
        del self._data[name]
    
    def __getitem__(self, name):
        return self.__getattr__(name)
    
    def __contains__(self, name):
        return self.__hasattr__(name)
    
    def __setitem__(self, name, value):
        self.__setattr__(name, value)
    
    def __delitem__(self, name):
        self.__delattr__(name)
    
    def __eq__(self, other):
        return isinstance(other, JSONDict) \
            and self._type_name == other._type_name \
            and self._template == other._template \
            and self._data == other._data

    def __repr__(self):
        return f'{self._type_name}: {self._data}'
    
    def __str__(self):
        return self.__repr__()
    
    def _copy(self):
        return JSONDict(self._type_name, deepcopy(self._template), deepcopy(self._data))
    
    def print(self):
        print(dumps(self._data, indent=4))


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
            if _is_list(self._item_template) or isinstance(self._item_template, dict):
                self.__getitem__(index)._type_check()
    
    def __getitem__(self, index):
        item = self._data[index]
        name = self._item_type_name
        if isinstance(self._item_template, dict) or (self._item_template is None and isinstance(item, dict)):
            dict_template = self._item_template
            if dict_template == {}:
                dict_template = None
            return JSONDict(name, dict_template, item)
        elif _is_list(self._item_template) or (self._item_template is None and isinstance(item, list)):
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
        if _is_list(self._item_template) and self._item_template != []:
            JSONList(self._item_type_name, self._item_template[0], value)
    
    def __setitem__(self, index, value):
        if isinstance(value, JSONDict) or isinstance(value, JSONList):
            value = value._data
        self._recursive_check_types(value)
        self._data[index] = value
    
    def __delitem__(self, index):
        del self._data[index]
    
    def append(self, value):
        self._recursive_check_types(value)
        self._data.append(value)

    def __eq__(self, other):
        return isinstance(other, JSONList) \
            and self._type_name == other._type_name \
            and self._item_template == other._item_template \
            and self._data == other._data
    
    def __repr__(self):
        return f'{self._type_name}: {self._data}'
    
    def __str__(self):
        return self.__repr__()
    
    def _copy(self):
        return JSONDict(self._type_name, deepcopy(self._item_template), deepcopy(self._data))
    
    def print(self):
        print(dumps(self._data, indent=4))    


def calculate_delta(old, new):
    if old._type_name != new._type_name or old._template != new._template:
        raise TypeError('Cannot calculate delta for data of different types')

    type_name = old._type_name
    template = old._template
    delta = JSONDict(type_name, template, {})
    for name in template:
        if name in old and name in new:
            old_value = old[name]
            new_value = new[name]
            if isinstance(old_value, JSONDict) and isinstance(new_value, JSONDict):
                if new_value._type_name != old_value._type_name or new_value._template != old_value._template:
                    delta[name] = new_value
                elif new_value._data != old_value._data:
                    delta[name] = calculate_delta(old_value, new_value)
            elif isinstance(old_value, JSONList) and isinstance(new_value, JSONList):
                if new_value._data != old_value._data:
                    delta[name] = new_value
            elif new_value != old_value:
                delta[name] = new_value
        elif name in old:
            delta[name] = None
        elif name in new:
            delta[name] = new_value
    
    return delta


def add_delta(old, delta):
    new = old._copy()
    for name in delta._data:
        value = delta[name]
        if value is None and name in new:
            del new[name]
        elif isinstance(value, JSONDict):
            new[name] = add_delta(new[name], value)
        else:
            new[name] = value
    return new
