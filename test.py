# from database import Database
from id_tools import *
from json_interface import *

# db = Database()
# db.setup()

# br1 = db.main_branch()
# db.update(br1, {})
# db.commit(br1)
# br2 = db.new_branch(db.root(), 'br2')
# db.update(br2, {})
# better = db.commit(br2)
# db.update(br1, {})
# bi = db.commit(br1)
# br3 = db.new_branch(bi, 'br3')
# rev = db.setup_revision(bi)
# db.update(br1, {})
# db.commit(br1)
# db.update(br3, {})
# ce = db.commit(br3)
# db.revise(rev, better)
# db.merge(br1, ce, {}, {})

class A:
    def __init__(self, x):
        self.x = x

    def set_y(self):
        self.y = 1
        
x = A(3)
x.set_y()

# db.data.print()

# print('--------------------')
# print(db._trace_back('v,da', include_revisions=True)[2])

# TODO test creating revisions on each input to a merge