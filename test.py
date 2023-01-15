import sys, inspect, os.path

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
path = os.path.dirname(path)
sys.path.append(path)

import yearbook_core as core
