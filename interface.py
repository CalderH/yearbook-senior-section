import yearbook_setup
import json_interface
import re
import inspect
import json
import typing
from typing import Annotated, Callable, Any
from dataclasses import dataclass
import ids


with open(yearbook_setup.core_path('interface template')) as file:
    interface_template = json.load(file)
interface_path = yearbook_setup.school_path('interface')
interface = json_interface.JSONFile(interface_path, 'interface', interface_template)

def add_interaction(value):
	interface.insert(1, value)

global current_item
global prompts_to_add


input_box = '    '

def box_filled(box):
	return box.strip() != ''


@dataclass
class Command:
	function: Callable
	parameters: dict[str, Any] # description, default value
	display_name_to_param_name: dict[str, str] # lets you get the actual parameter names from the descriptions

@dataclass
class Prompt(Command):
	text: str
	id: str

next_prompt_id = ids.start_sequence

command_dict = {}
prompt_dict = {}

def add_command(name, function):
	if name in command_dict:
		disambiguator = 1
		while name + str(disambiguator) in command_dict:
			disambiguator += 1
		name += str(disambiguator)
	command_dict[name] = function

def standardize_command_name(name):
	return re.sub('[_\s]+', ' ', name).lower().strip()


class CommandException(Exception):
	pass
	

def tn(type, name):
	return Annotated[type, name]


def cmd(name=None, category=None):
	def command_decorator(fun):
		wrapped_fun = fun

		# TODO: deal with the possibility that two parameters are annotated with the exact same description

		command_names = [fun.__name__.replace('_', ' ')]

		fun_name = fun.__name__

		acronym = ''.join(re.findall(r'(?:^|_)(\w)', fun_name))
		if acronym in command_dict:
			disambiguator = 1
			while acronym + str(disambiguator) in command_dict:
				disambiguator += 1
			acronym += str(disambiguator)
			command_names.append(acronym)
		
		if name is not None:
			if isinstance(name, str):
				command_names.append(name)
			else:
				command_names += name

		command_parameters = []
		display_name_to_param_name = {}
		fun_parameters = inspect.signature(fun).parameters

		for param_name, param_info in fun_parameters.items():
			annotation = param_info.annotation
			if annotation == inspect.Parameter.empty:
				param_key = param_name
			elif isinstance(annotation, str):
				param_key = annotation
			else:
				if isinstance(annotation, typing._AnnotatedAlias):
					param_display_name = annotation.__metadata__[1]
					param_type = annotation.__origin__
				else:
					param_display_name = param_name
					param_type = annotation

				if param_type in json_interface.type_names:
					param_type_name = json_interface.type_names[json_interface.type_names]
				else:
					param_type_name = str(param_type)

				param_key = f'{param_display_name} ({param_type_name})'
			
			if param_key in command_parameters:
				raise Exception(f'Duplicate parameter "{param_key}" in {fun_name}')
			
			default = param_info.default
			if default == inspect.Parameter.empty:
				default = None
			
			command_parameters[param_key] = default
			display_name_to_param_name[param_key] = name
		
		command_obj = Command(wrapped_fun, command_parameters, display_name_to_param_name)

		for name in command_names:
			add_command(name, command_obj)

		return fun
	
	return command_decorator


command = cmd()


def prompt(text):
	def prompt_decorator(fun):
		id = next_prompt_id
		next_prompt_id = ids.next_id(next_prompt_id)
		prompt_dict[id] = Prompt(fun, text, id)
		
		return fun

	return prompt_decorator


def respond_to_item(index):
	global current_item, prompts_to_add
	current_item = interface[index]
	prompts_to_add = []

	if isinstance(current_item, str):
		if not box_filled(current_item):
			return
		
		else:
			standardized_name = standardize_command_name(current_item)

			if standardized_name in command_dict:
				command = command_dict[standardized_name]
				
				if len(command.parameters) == 0:
					current_item['redo?'] = input_box
					current_item['copy?'] = input_box
					command.function()
				else:
					new_item = {'command': standardized_name,
								'inputs': command.parameters,
								'done?': input_box}
					add_interaction(new_item)

			else:
				name_error = {'command': current_item,
					          'error': 'There is no command with this name. Try reentering a correct name, and type in the redo field to try again. (For a list of commands, enter "help".)',
							  'redo?': input_box}
				add_interaction(name_error)
			
	elif isinstance(current_item, json_interface.JSONDict):
		if 'command' in current_item:
			command_obj = command_dict[current_item.command]
		else:
			command_obj = prompt_dict[current_item.prompt_id]
		
		# Command with all inputs
		if 'done' in current_item and box_filled(current_item['done?']):
			del current_item['done?']
			current_item['redo?'] = input_box
			current_item['copy?'] = input_box
			command_obj.function(**current_item.inputs)

		# Incorrect command name
		elif 'inputs' not in current_item:
			if box_filled(current_item['redo?']):
				standardized_name = standardize_command_name(current_item.command)

				if standardized_name in command_dict:
					command = command_dict[standardized_name]
				
					if len(command.parameters) == 0:
						current_item['redo?'] = input_box
						current_item['copy?'] = input_box
						command.function()
					else:
						current_item.command = standardized_name
						current_item.inputs = command.parameters
						current_item['done?'] = input_box
						del current_item['redo?']
				else:
					current_item['redo?'] = input_box

		# Completed command that could be used again
		elif box_filled(current_item['redo?']):
			current_item['redo?'] = input_box
			command_obj.function(**current_item.inputs)
		elif box_filled(current_item['copy?']):
			current_item['copy?'] = input_box
			new_interaction = current_item.copy()
			del new_interaction['redo?']
			del new_interaction['copy?']
			new_interaction['done?'] = input_box
			add_interaction(new_interaction)
	
	elif isinstance(current_item, json_interface.JSONList):
		


def output(s):
	global current_item_index

	item = interface[current_item_index]
	if 'output' in item:
		item.output += '\n' + s
	else:
		item.output = s


def error(s):
	global current_item_index

	item = interface[current_item_index]
	if 'error' in item:
		item.error += '\n' + s
	else:
		item.error = s
