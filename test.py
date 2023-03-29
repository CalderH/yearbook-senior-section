from database import Database
from id_tools import *
from json_interface import *

db = Database()
db.setup()

db.change_open_version('b,ba', {})
db.commit('b,ba')
db.change_open_version('b,ba', {})
db.commit('b,ba')
db.change_open_version('b,ba', {})
db.commit('b,ba')

# db.data.print()

print(db._ancestry('v,bo'))

