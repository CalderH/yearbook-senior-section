import json

# __all__ = ['system_settings', 'year_settings']

with open('settings.json') as system_settings_file:
    system_settings = json.load(system_settings_file)

with open(system_settings['settings path']) as year_settings_file:
    year_settings = json.load(year_settings_file)
