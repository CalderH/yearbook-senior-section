from database import Database
from id_tools import *
from json_interface import *

template = {"": {"name": "", "age": 0}}
old_value = {"ba": {"name": "a", "age": 1}, "be": {"name": "e", "age": 2}, "bi": {"name": "i", "age": 3}}
new_value = {"ba": {"name": "aa", "age": 1}, "be": {"name": "e", "age": 4}, "bo": {"name": "o", "age": 100}}
old = JSONDict('thing', template, old_value)
new = JSONDict('thing', template, new_value)
print(calculate_delta(old, new))

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


# db.data.print()

# print('--------------------')
# print(db._trace_back('v,da', include_revisions=True)[2])

# TODO test creating revisions on each input to a merge