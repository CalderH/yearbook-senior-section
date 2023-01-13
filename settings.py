import json
import os.path

with open('settings.json') as system_settings_file:
    system_settings = json.load(system_settings_file)

year_settings_path = system_settings['settings path']
with open(year_settings_path) as year_settings_file:
    year_settings = json.load(year_settings_file)

def path_to(key, *args):
    return os.path.join(year_settings_path, year_settings['root'], year_settings[key], *args)

with open('student template.json') as file:
    student_template = json.load(file)
