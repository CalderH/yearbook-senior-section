import yearbook_setup
import json_interface
import re
import inspect
import json
import typing
from typing import Annotated, Callable, Any
import ids


with open(yearbook_setup.core_path('interface template')) as file:
    interface_template = json.load(file)
interface_path = yearbook_setup.school_path('interface')
interface = json_interface.JSONFile(interface_path, 'interface', interface_template)

def add_interaction(value):
	interface.insert(1, value)

global prompts_to_add


input_box = '    '

def box_filled(box):
	return box.strip() != ''


next_prompt_id = ids.start_sequence

command_dict = {}
prompt_dict = {}


class Command:
	def __init__(self, function):
		parameters = {}
		display_name_to_param_name = {}
		fun_parameters = inspect.signature(function).parameters

		for param_name, param_info in fun_parameters.items():
			annotation = param_info.annotation
			if annotation == inspect.Parameter.empty:
				param_key = param_name
			elif isinstance(annotation, str):
				param_key = annotation
			else:
				if isinstance(annotation, typing._AnnotatedAlias):
					param_display_name = annotation.__metadata__[0]
					param_type = annotation.__origin__
				else:
					param_display_name = param_name
					param_type = annotation

				if param_type in json_interface.type_names:
					param_type_name = json_interface.type_names[param_type]
				else:
					param_type_name = str(param_type)

				param_key = f'{param_display_name} ({param_type_name})'
			
			if param_key in parameters:
				raise Exception(f'Duplicate parameter "{param_key}" in {function.__name__}')
			
			default = param_info.default
			if default == inspect.Parameter.empty:
				default = None
			
			parameters[param_key] = default
			display_name_to_param_name[param_key] = param_name

		self.function = function
		self.parameters = parameters
		self.display_name_to_param_name = display_name_to_param_name


class Prompt(Command):
	def __init__(self, function, text):
		super().__init__(function)

		self.text = text
		
		self.id = next_prompt_id
		next_prompt_id = ids.next_id(next_prompt_id)
		prompt_dict[self.id] = self


def add_command(name, command_obj):
	if name in command_dict:
		disambiguator = 1
		while name + str(disambiguator) in command_dict:
			disambiguator += 1
		name += str(disambiguator)
	command_dict[name] = command_obj

def standardize_command_name(name):
	return re.sub('[_\s]+', ' ', name).lower().strip()

def disambiguate(name):
	if name in command_dict:
		disambiguator = 1
		while name + str(disambiguator) in command_dict:
			disambiguator += 1
		return name + str(disambiguator)
	else:
		return name


class CommandException(Exception):
	pass
	

def tn(type, name):
	return Annotated[type, name]


def cmd(name=None, category=None):
	def command_decorator(fun):
		command_names = [disambiguate(fun.__name__.replace('_', ' '))]

		fun_name = fun.__name__

		acronym = disambiguate(''.join(re.findall(r'(?:^|_)(\w)', fun_name)))
		command_names.append(acronym)
		
		if name is not None:
			if isinstance(name, str):
				command_names.append(disambiguate(name))
			else:
				command_names += [disambiguate(individual_name) for individual_name in name]

		command_obj = Command(fun)

		for command_name in command_names:
			add_command(command_name, command_obj)

		return fun
	
	return command_decorator


command = cmd()


def prompt(text):
	def prompt_decorator(fun):
		Prompt(fun, text)
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
		respond_to_dict(current_item)
	
	elif isinstance(current_item, json_interface.JSONList):
		...


def respond_to_command(command_name):
	standardized_name = standardize_command_name(command_name)
	item = {}

	if standardized_name in command_dict:
		command = command_dict[standardized_name]
		item['command'] = standardized_name

		if len(command.parameters) == 0:
			item['redo?'] = input_box
			item['copy?'] = input_box

			execute_command(command, )
			command.function()
			if prompts_to_add != []:
				item = [item] + 
		else:
			item['inputs'] = command.parameters
			item['done?'] = input_box
	else:
		item['command'] = command_name
		item['error'] = 'There is no command with this name. Try reentering a correct name, and type in the redo field to try again. (For a list of commands, enter "help".)'
		item['redo?'] = input_box
	
	return item


def execute_command(command, interaction, context_list, context_index):
	command.function(**interaction.inputs)

	if prompts_to_add != []:
		prompt_interactions = []
		for prompt in prompts_to_add:
			prompt_interaction = {}
			prompt_interaction['prompt'] = prompt.text
			prompt_interaction['inputs'] = prompt.parameters
			prompt_interaction['done?'] = input_box
			prompt_interaction['prompt id'] = prompt.id
			prompt_interactions.append(prompt_interaction)
		
		if context is None:
			context_maker = interface.new()
			context_maker.append([])
			context = context_maker[0]
		
		context.append


def respond_to_dict(item, context=None):
	if 'command' in item:
		command_obj = command_dict[item.command]
	else:
		command_obj = prompt_dict[item.prompt_id]
	
	# Command with all inputs
	if 'done' in item and box_filled(item['done?']):
		del item['done?']
		item['redo?'] = input_box
		item['copy?'] = input_box
		command_obj.function(**item.inputs)

	# Incorrect command name
	elif 'inputs' not in item:
		if box_filled(item['redo?']):
			standardized_name = standardize_command_name(item.command)

			if standardized_name in command_dict:
				command = command_dict[standardized_name]
			
				if len(command.parameters) == 0:
					item['redo?'] = input_box
					item['copy?'] = input_box
					command.function()
				else:
					item.command = standardized_name
					item.inputs = command.parameters
					item['done?'] = input_box
					del item['redo?']
			else:
				item['redo?'] = input_box

	# Completed command that could be used again
	elif box_filled(item['redo?']):
		item['redo?'] = input_box
		command_obj.function(**item.inputs)
	elif box_filled(item['copy?']):
		item['copy?'] = input_box
		new_interaction = item.copy()
		del new_interaction['redo?']
		del new_interaction['copy?']
		new_interaction['done?'] = input_box
		add_interaction(new_interaction)


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
