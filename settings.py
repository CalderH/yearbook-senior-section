import json

with open('settings.json') as system_settings_file:
    system_settings = json.load(system_settings_file)

year_settings_path = system_settings['settings path']
with open(year_settings_path) as year_settings_file:
    year_settings = json.load(year_settings_file)

def path_to(key, *args):
    path = year_settings[key]
    if path[0] != '/':
        path = year_settings_path + '/' + year_settings['root'] + '/' + path
    if len(args) > 0:
        if path[-1] != '/':
            path += '/'
            path += '/'.join(args)
    return path

def template_path():
    return path_to('template')
