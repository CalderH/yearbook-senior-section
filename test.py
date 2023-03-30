from database import Database
from id_tools import *
from json_interface import *

db = Database()
db.setup()

br1 = db.main_branch()
db.update(br1, {})
db.commit(br1)
db.update(br1, {})
db.commit(br1)
br2 = db.new_branch(db.root(), 'br2')
db.update(br2, {})
db.commit(br2)
db.update(br1, {})
bi = db.commit(br1)
br3 = db.new_branch(bi, 'br3')
rev = db.setup_revision(bi)
db.revise(rev, 'v,bo')
db.update(br1, {})
db.commit(br1)
db.update(br3, {})
ce = db.commit(br3)
db.merge(br1, ce, {}, {})


db.data.print()

print('--------------------')
print(db._ancestry('v,co'))

# TODO can I make a branch from an open version