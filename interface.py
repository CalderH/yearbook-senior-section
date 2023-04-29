import yearbook_setup
import json_interface
import re
import inspect
import json
from typing import List, Annotated, Optional

with open(yearbook_setup.core_path('interface template')) as file:
    interface_template = json.load(file)
interface_path = yearbook_setup.school_path('interface')

interface = json_interface.JSONFile(interface_path, 'interface', interface_template)

command_dict = {}
# command_lists = {}

class CommandException(Exception):
	pass
	
def create_interaction():
	...

def output():
	...

def tn(type, name):
	return Annotated[type, name]

def comm(name=None, category=None, state=None):
	def command_decorator(fun):
		wrapped_fun = fun

		command_names = []
		command_names.append(fun.__name__.replace('_', ' '))

		acronym = ''.join(re.findall(r'(?:^|_)(\w)', fun.__name__))
		if acronym in command_dict:
			disambiguator = 1
			while acronym + str(disambiguator) in command_dict:
				disambiguator += 1
			acronym += str(disambiguator)
			command_names.append(acronym)
		
		# add name(s) from decorator as well


		return fun
	return command_decorator