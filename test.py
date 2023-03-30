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
db.update('b,be', {})
db.commit('b,be')
db.setup_revision('v,bo')
db.revise('v,ce', 'b,be')
db.update('b,ba', {})
db.commit('b,ba')
db.revise('v,ce', 'v,ba')
db.update('b,ba', {})
db.commit('b,ba')

db.data.print()

print('--------------------')
print(db._revision_state('v,bo'))
print(db._revision_state('v,bu'))
print(db._revision_state('v,ci'))


# TODO can I make a branch from an open version