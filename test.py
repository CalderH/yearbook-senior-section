from time import sleep
import os.path
import threading

def monitor(path):
    name = os.path.basename(path)
    def f():
        last_mtime = None
        while(True):
            mtime = os.path.getmtime(path)
            if last_mtime is not None and mtime != last_mtime:
                print(f'edited {name}!')
            last_mtime = mtime
            sleep(0.1)
    thread = threading.Thread(target=f)
    thread.start()


p1 = '/Users/calder/Documents/School/Brown/Yearbook/Senior section code/other/planning.txt'
p2 = '/Users/calder/Documents/School/Brown/Yearbook/Senior section code/yearbook_core/test.py'

monitor(p1)
monitor(p2)
