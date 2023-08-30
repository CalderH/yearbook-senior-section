from json_interface import JSONFile
from time import sleep
import os.path
import threading

# def monitor(path):
#     name = os.path.basename(path)
#     def f():
#         last_mtime = None
#         while True:
#             mtime = os.path.getmtime(path)
#             if last_mtime is not None and mtime != last_mtime:
#                 print(f'edited {name}!')
#             last_mtime = mtime
#             sleep(0.1)
#     thread = threading.Thread(target=f)
#     thread.start()

def start_monitor(path, action):
    def monitor():
        last_mtime = None
        while True:
            mtime = os.path.getmtime(path)
            if last_mtime is not None and mtime != last_mtime:
                sleep(0.1)
                action()
            last_mtime = os.path.getmtime(path)
            sleep(0.1)

    thread = threading.Thread(target=monitor)
    thread.start()


def start_json_monitor(json_file, json_action):
    def action():
        json_file.load()
        json_action(json_file)
        json_file.save()
    start_monitor(json_file.path, action)


def start_json_monitor_from_parameters(path, type_name, template, json_action):
    json_file = JSONFile(path, type_name, template)
    start_json_monitor(json_file, json_action)

# TODO If I’m going to work on this anymore at some point,
# make it so that I can compare this version with the previously saved version.
# Might actually require updating JSONFile. but I won’t deal with that now.