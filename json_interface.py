import json
from copy import deepcopy
from typing import Union, Optional, Any, cast, Callable, Dict
import os


RawValue = Union[None, int, float, bool, str, list, dict]
Value = Union[RawValue, 'JSONValue']


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

def _is_list(template: RawValue) -> bool:
    """Returns whether this template represents a list."""

    return isinstance(template, list) and len(template) <= 1


def _type_name(value, template=False, collapse_choice=False) -> str:
    """Returns the name of the type of a given value.
    
    Interprets lists differently depending on whether the input is a template or data
    For data (template is False), all lists are given type 'list'
    For a template (template is True), lists with more than one element are interpreted as 'choice's of multiple options
    And if collapse_choice is True, choices where all elements have the same type are interpreted as that type
    """

    type_names = {int: 'number', float: 'number', bool: 'boolean', str: 'string', list: 'list', dict: 'dict', type(None): 'none'}
    if template and type(value) == list:
        if len(value) <= 1:
            return 'list'
        elif collapse_choice and len(set([_type_name(item, template=True, collapse_choice=True) for item in value])) == 1:
            return _type_name(value[0], template=True, collapse_choice=True)
        else:
            return 'choice'
    else:
        return type_names[type(value)]


def _recursive_in(e, l: list) -> bool:
    """Determine whether an element is in a list or in a sublist of (a sublist of…) that list"""

    for le in l:
        # Have to make the type check — otherwise it would say that True is in [1]
        if e == le and type(e) == type(le):
            return True
    return any(_recursive_in(e, le) for le in l if isinstance(le, list))


def _type_check(name: str, data: RawValue, template: RawValue) -> None:
    """Check if a piece of data matches a template."""

    # Null template matches everything
    # Everything matches null data
    if template is None or data is None:
        return

    data_type_name = _type_name(data)
    template_type_name = _type_name(template, template=True)

    # If the template represents multiple options for a single value
    if template_type_name == 'choice':
        # Template is guaranteed to be a list now; tell that to the type checker
        template = cast(list, template)

        # Get the type name for everything in the template
        template_type_names: list[str] = [_type_name(option, template=True, collapse_choice=True) for option in template]

        # If all the options in the template have the same type,
        # then just check whether the value is equal to one of those options
        if len(set(template_type_names)) == 1:
            if not _recursive_in(data, template):
                raise TypeError(f'{name} must be one of {template}; it cannot be {repr(data)}')
            
        # Otherwise we need to check if the value matches the type and structure of one of those options
        else:
            # Check the value against each option one by one
            # found_type keeps track of whether we've at least matched something of the right type (to give more informative error messages)
            found_type = False
            for option in template:
                if _type_name(option, template=True, collapse_choice=True) == data_type_name:
                    found_type = True
                
                # If this option has the right type, we're done, otherwise keep going
                try:
                    _type_check(name, data, option)
                    return
                except:
                    continue
            if found_type:
                raise TypeError(f'{name} must match one of {template}; it cannot be {repr(data)}')
            else:
                raise TypeError(f'{name} must be one of the types {set(template_type_names)}; it cannot be {repr(data)}')   
    else:
        # If the template only has one option

        if data_type_name != template_type_name:
            raise TypeError(f'{name} must be a {template_type_name}; it cannot be {repr(data)}')
        
        if data_type_name == 'dict':
            template = cast(dict, template)
            data = cast(dict, data)
            # Creating the dict will cause it to type-check itself
            JSONDict(name, template, data)

        elif data_type_name == 'list':
            template = cast(list, template)
            data = cast(list, data)
            # Creating the list will cause it to type-check itself
            JSONList(name, template[0], data)


class JSONValue:
    # TODO, maybe: make some functions or values implemented here, like data
    pass


class JSONDict(JSONValue):
    # Need this to prevent getattr from recurring infinitely
    reserved_names = ['_type_name', '_template', '_any_keys', '_data', '_callback', '_static']

    def __init__(self, type_name: str, template: Optional[dict], data: dict, callback: Optional[Callable] = None, static: bool = False):
        self._type_name: str = type_name
        self._template: Optional[dict] = template
        # If _any_keys is true, this represents a dict that holds data for arbitrary keys,
        # rather than specified attributes
        self._any_keys: bool = template is not None and template.keys() == {''}
        self._data: dict = deepcopy(data)
        self._callback = callback
        self._static = static

        self._type_check()
    
    def _element_type_name(self, name: str) -> str:
        """Helper for error messages"""

        if self._any_keys:
            return f'(element of {self._type_name})'
        else:
            return f'{self._type_name}.{name}'
        
    def _check_name(self, name) -> None:
        """Check whether the template has an attribute with a given name

        Returns nothing on success, raises exception on failure.
        (Succeeds if _any_keys is true)"""

        if self._template is not None and not self._any_keys and name not in self._template:
            raise AttributeError(f'{self._type_name} has no attribute \'{name}\'')

    def _type_check(self) -> None:
        """Checks whether each name/value pair matches the template.
        
        Returns nothing on success, raises exception on failure."""

        # Null template matches everything
        if self._template is None or self._template == {}:
            return
        
        # Everything matches null data
        if self._data is None:
            return
        
        template_value = None
        # If the dict stores the same template of data for arbitrary keys, then get that template
        if self._any_keys:
            template_value = self._template['']

        # Check each name/value pair
        for name, data_value in self._data.items():
            # Check name
            self._check_name(name)
            # Get the value template, if we haven't already
            if not self._any_keys:
                template_value = self._template[name]
            # Type check the data value with the template value
            _type_check(self._element_type_name(name), data_value, template_value)


            try:
                if _is_list(template_value) or isinstance(template_value, dict):
                    # Creates a JSONDict or JSONList, which type-check themselves in the __init__ function 
                    self.__getattr__(name)
            except:
                raise Exception('I guess you do actually need to check this?')
    
    def _check_static(self):
        if self._static:
            raise TypeError('Cannot edit a static JSONDict')

    def make_static(self):
        self._static = True
    
    def make_mutable(self):
        self._static = False

    def __getattr__(self, name: str) -> Value:
        if name in JSONDict.reserved_names:
            return super().__getattribute__(name)
        else:
            return self[name]
    
    def __hasattr__(self, name: str) -> bool:
        return name in self._data and self._data[name] is not None
    
    def _iter_dict(self):
        return {name: value for name in self._data if (value := self[name]) is not None}

    def __iter__(self):
        # When you iterate through the JSONDict, you only want the ones with non-None value
        return iter(self._iter_dict())
    
    def items(self):
        return self._iter_dict().items()
    
    def keys(self):
        return self._iter_dict().keys()
    
    def values(self):
        return self._iter_dict().values()
    
    def _do_callback(self) -> None:
        if self._callback is not None:
            self._callback()

    def __setattr__(self, name: str, value: Value) -> None:
        if name in JSONDict.reserved_names:
            super().__setattr__(name, value)
        else:
            self[name] = value
    
    def __delattr__(self, name: str) -> None:
        if name in JSONDict.reserved_names:
            super().__delattr__(name)
        else:
            self.__delitem__(name)
    
    def __getitem__(self, name: str) -> Value:
        # For legibility, names in the JSON file have spaces; those are represented as underscores here
        name = underscores_to_spaces(name)
        # First check the name
        self._check_name(name)

        if name in self._data:
            # Get the value, then type check it
            # (Not strictly necessary, since setattr also checks)

            data_value = self._data[name]
            if data_value is None:
                return None
            
            # Figure out what template value to compare the 
            if self._template is None:
                template_value = None
            elif self._any_keys:
                template_value = self._template['']
            else:
                template_value = self._template[name]
            
            # If the result is a dict or a list, return a JSONDict or JSONList
            if isinstance(template_value, dict) or (template_value is None and isinstance(data_value, dict)):
                if template_value == {}:
                    template_value = None
                return JSONDict(self._element_type_name(name), template_value, data_value, callback=self._callback, static=self._static)
            elif _is_list(template_value) or (template_value is None and isinstance(data_value, list)):
                if template_value is None or template_value == []:
                    item_template = None
                else:
                    item_template = template_value[0]
                return JSONList(self._element_type_name(name), item_template, data_value, callback=self._callback, static=self._static)
            # Otherwise just return the raw value
            else:
                return data_value
        # If there is nothing with this name, but there could be, return None rather than an error
        else:
            return None
    
    def __contains__(self, name: str) -> bool:
        return self.__hasattr__(name)
    
    def __setitem__(self, name: str, value: Value) -> None:
        self._check_static()

        name = underscores_to_spaces(name)

        if isinstance(value, JSONDict) or isinstance(value, JSONList):
            value = value._data
        
        # Only need to type check if the template is not none
        if self._template is not None:
            self._check_name(name)
            type_name = self._element_type_name(name)
            if self._any_keys:
                template_value = self._template['']
            else:
                template_value = self._template[name]
            _type_check(type_name, value, template_value)


            try:
                if isinstance(template_value, dict) and template_value != {}:
                    JSONDict(type_name, template_value, value)
                if _is_list(template_value) and template_value != []: # TODO can it also be [None]?
                    JSONList(type_name, template_value[0], value)
            except:
                raise Exception('I guess you do actually need to check this?')
        
        # Once we've type checked, can actually set the value
        self._data[name] = value
        self._do_callback()
    
    def __delitem__(self, name: str) -> None:
        self._check_static()
        name = underscores_to_spaces(name)
        self._check_name(name)
        del self._data[name]
        self._do_callback()
    
    def set_data(self, new_data: dict) -> None:
        self._check_static()
        """Sets the data of this object to new data"""

        # First try creating a new object with this data. If the type check fails, then this object's data will not be impacted.
        JSONDict(self._type_name, self._template, new_data)
        self._data = new_data

    def __len__(self) -> int:
        return len(self._iter_dict())

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, JSONDict):
            return     self._type_name == other._type_name \
                   and self._template == other._template \
                   and self._data == other._data
        elif isinstance(other, dict):
            return self._data == other
        else:
            return False

    def _template_order(self) -> dict:
        output = {}
        
        if self._any_keys:
            keys = sorted(list(self._data.keys()))
        else:
            keys = list(self._template.keys())
        
        for key in keys:
            value = self[key]
            if value is None:
                continue
            if isinstance(value, JSONDict) or isinstance(value, JSONList):
                value = value._template_order()
            output[key] = value

        return output
        
    def __repr__(self) -> str:
        return f'{self._type_name}: {self._template_order()}'
    
    def __str__(self) -> str:
        return self._template_order().__repr__()
    
    def copy(self) -> 'JSONDict':
        return JSONDict(self._type_name, deepcopy(self._template), deepcopy(self._data), callback=self._callback, static=self._static)
    
    def new(self, callback=None) -> 'JSONDict':
        """Create a new empty, mutable JSONDict with the same type name and template"""

        return JSONDict(self._type_name, deepcopy(self._template), {}, callback=callback)
    
    def print(self) -> None:
        print(json.dumps(self._template_order(), indent=4))


class JSONList(JSONValue):
    def __init__(self, type_name: str, item_template: RawValue, data: list, callback: Optional[Callable] = None, static: bool = False):
        self._type_name: str = type_name
        self._item_template: RawValue = item_template
        self._data: list = deepcopy(data)
        self._item_type_name: str = f'(item of {self._type_name})'
        self._callback = callback
        self._static = static

        self._type_check()
    
    def _type_check(self) -> None:
        """Checks whether each item matches the item template.
        
        Returns nothing on success, raises exception on failure.
        """

        # Null item template matches everything
        if self._item_template is None:
            return

        for index in range(len(self._data)):
            item = self._data[index]
            self._type_check_item(item)


            try:
                if _is_list(self._item_template) or isinstance(self._item_template, dict):
                    self.__getitem__(index)._type_check()
            except:
                raise Exception('I guess you do actually need to check this?')
    
    def _check_static(self):
        if self._static:
            raise TypeError('Cannot edit a static JSONList')
    
    def make_static(self):
        self._static = True
    
    def make_mutable(self):
        self._static = False

    def __getitem__(self, index: int) -> Value:
        if index in self._children_objects:
            return self._children_objects[index]

        item = self._data[index]
        name = self._item_type_name

        # If the result is a dict or a list, return a JSONDict or JSONList
        if isinstance(self._item_template, dict) or (self._item_template is None and isinstance(item, dict)):
            dict_template = self._item_template
            if dict_template == {}:
                dict_template = None
            return JSONDict(name, dict_template, item, callback=self._callback, static=self._static)
        elif _is_list(self._item_template) or (self._item_template is None and isinstance(item, list)):
            if self._item_template is None or self._item_template == []:
                item_template = None
            else:
                self._item_template = cast(list, self._item_template)
                item_template = self._item_template[0]
            return JSONList(name, item_template, item, callback=self._callback, static=self._static)
         # Otherwise just return the raw value
        else:
            return item
    
    def _type_check_item(self, value: RawValue) -> None:
        """Check the type of an item or candidate item"""

        _type_check(self._item_type_name, value, self._item_template)


        try:
            if isinstance(self._item_template, dict) and self._item_template != {}:
                JSONDict(self._item_type_name, self._item_template, value)
            if _is_list(self._item_template) and self._item_template != []:
                JSONList(self._item_type_name, self._item_template[0], value)
        except:
            raise Exception('I guess you do actually need to check this?')
    
    def _do_callback(self) -> None:
        if self._callback is not None:
            self._callback()

    def __setitem__(self, index: int, value: Value) -> None:
        self._check_static()
        if isinstance(value, JSONDict) or isinstance(value, JSONList):
            value = value._data
        self._type_check_item(value)
        self._data[index] = value
        self._do_callback()
    
    def __delitem__(self, index: int) -> None:
        self._check_static()
        del self._data[index]
        self._do_callback()
    
    def append(self, value: Value) -> None:
        self._check_static()
        if isinstance(value, JSONDict) or isinstance(value, JSONList):
            value = value._data

        self._type_check_item(value)
        self._data.append(value)
        self._do_callback()

    def remove(self, value: Value) -> None:
        self._check_static()
        if isinstance(value, JSONDict) or isinstance(value, JSONList):
            value = value._data
        
        if value in self._data:
            self._data.remove(value)

    def set_data(self, new_data: list) -> None:
        """Sets the data of this object to new data"""

        self._check_static()
        
        # First try creating a new object with this data. If the type check fails, then this object's data will not be impacted.
        JSONList(self._type_name, self._item_template, new_data)
        self._data = new_data

    def __contains__(self, item) -> bool:
        if isinstance(item, JSONDict) or isinstance(item, JSONList):
            item = item._data
        
        return item in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, JSONList):
            return     self._type_name == other._type_name \
                   and self._item_template == other._item_template \
                   and self._data == other._data
        elif isinstance(other, list):
            return self._data == other
        else:
            return False
    
    def _template_order(self) -> list:
        output = []

        for item in self:
            if isinstance(item, JSONDict) or isinstance(item, JSONList):
                output.append(item._template_order())
            else:
                output.append(item)
        
        return output

    def __repr__(self) -> str:
        return f'{self._type_name}: {self._template_order()}'
    
    def __str__(self) -> str:
        return self.__repr__()

    def copy(self) -> 'JSONList':
        return JSONList(self._type_name, deepcopy(self._item_template), deepcopy(self._data), callback=self._callback, static=self._static)
    
    def new(self, callback=None) -> 'JSONList':
        """Create a new empty, mutable JSONList with the same type name and template"""

        return JSONList(self._type_name, deepcopy(self._item_template), [], callback=callback)
    
    def print(self):
        print(json.dumps(self._template_order(), indent=4))    


def calculate_delta(old: JSONDict, new: JSONDict) -> JSONDict:
    """Given two JSONDicts, return a new JSONDict representing the difference between them.

    If an attribute is added or changed in the new dict, the delta contains the value of that attribute in the new dict.
    If an attribute was present in the old dict and is absent in the new dict, the delta maps that tribute to None.

    If a value is a dict, calculate_delta recurs on that dict.
    """

    if old._type_name != new._type_name or old._template != new._template:
        raise TypeError('Cannot calculate delta for data of different types')

    type_name = old._type_name
    template = old._template
    delta = JSONDict(type_name, template, {})

    # Go through all the names
    # First need to determine what names to look at
    if old._any_keys or template is None:
        names = old._data.keys() | new._data.keys()
    else:
        names = template.keys()

    for name in names:
        if name in old and name in new:
            old_value = old[name]
            new_value = new[name]
            if isinstance(old_value, JSONDict) and isinstance(new_value, JSONDict):
                if new_value._type_name != old_value._type_name or new_value._template != old_value._template:
                    delta[name] = new_value
                # If the old and new values are compatible dicts, recur on them
                elif new_value._data != old_value._data:
                    delta[name] = calculate_delta(old_value, new_value)
            # Does not recur on lists
            elif isinstance(old_value, JSONList) and isinstance(new_value, JSONList):
                if new_value._data != old_value._data:
                    delta[name] = new_value
            elif new_value != old_value:
                delta[name] = new_value
        elif name in old:
            delta[name] = None
        elif name in new:
            delta[name] = new[name]
    
    return delta


def add_delta(old: JSONDict, delta: JSONDict) -> JSONDict:
    """Applies changes to an old JSONDict to produce a new JSONDict.

    It should be the case that calculate_delta(A, B) = C if and only if add_delta(A, C) = B
    """

    new = old.copy()
    static = old._static
    new.make_mutable()
    for name in delta._data:
        delta_value = delta[name]
        # Need to check "name in new" to distinguish between a nonexistent attribute (Which returns None) and an attribute with value None
        if delta_value is None and name in new:
            del new[name]
        elif isinstance(delta_value, JSONDict):
            old_value = cast(JSONDict, new[name])
            new[name] = add_delta(old_value, delta_value)
        else:
            new[name] = delta_value
    new._static = static
    return new


class JSONFile:
    reserved_names = ['path', 'type_name', 'template', 'data']

    def __init__(self, path: str, type_name: str, template: RawValue):
        self.path: str = path
        self.type_name = type_name
        self.template = template
        if isinstance(template, dict):
            self.data = JSONDict(self.type_name, self.template, {})
        else:
            self.data = JSONList(self.type_name, self.template, [])
    
    def load(self):
        with open(self.path) as file:
            raw_data = json.load(file)

        if isinstance(raw_data, dict):
            self.data = JSONDict(self.type_name, self.template, raw_data)
        elif isinstance(raw_data, list):
            self.data = JSONList(self.type_name, self.template, raw_data)
        else:
            raise Exception('JSONFile requires that the top-level element be a list or dict')
    
    def save(self):
        with open(self.path, 'w') as file:
            json.dump(self.data._data, file, indent=4)
    
    def __getattr__(self, name):
        if name in JSONFile.reserved_names:
            return super().__getattribute__(name)
        else:
            return self.data.__getattr__(name)
    
    def __setattr__(self, name, value):
        if name in JSONFile.reserved_names:
            super().__setattr__(name, value)
        else:
            self.data.__setattr__(name, value)
        
    def __delattr__(self, name):
        if name in JSONFile.reserved_names:
            return super().__delattr__(name)
        else:
            return self.data.__delattr__(name)
