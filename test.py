from database import Database
from id_tools import *
from json_interface import *

db = Database()
db.setup()

db.update('b,ba', {})
db.commit('b,ba')
db.new_branch('v,ba', 'branch 2')
db.update('b,ba', {})
db.commit('b,ba')
db.update('b,ba', {})
db.commit('b,ba')
db.setup_revision('v,bo')
db.revise('v,ca', 'b,be')
db.update('b,ba', {})
db.commit('b,ba')
db.revise('v,ca', 'v,ba')
db.update('b,ba', {})
db.commit('b,ba')

db.data.print()

print('--------------------')
print(db._ancestry('v,bo'))
print(db._ancestry('v,bu'))
print(db._ancestry('v,ce'))


# TODO can I make a branch from an open version