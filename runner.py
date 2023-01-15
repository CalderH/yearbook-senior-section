import json
import os.path


def run():
    with open('settings.json') as file:
        settings = json.load(file)
    
    with open('paths.json') as file:
        paths = json.load(file)

    year_settings_path = paths['year settings']
    with open(year_settings_path) as file:
        year_settings = json.load(file)

    def path_to(key, *args):
        return os.path.normpath(os.path.join(year_settings_path, year_settings['root'], year_settings[key], *args))
    
    with open('student_template.json') as file:
        student_template = json.load(file)
    
    print(year_settings)
