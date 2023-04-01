from database import Database
from id_tools import *
from json_interface import *

from datetime import datetime
import json


with open('2022.json') as file:
    data = json.load(file)

d1 = JSONDict('all', None, data)
d2 = d1.copy()

start = datetime.now()

for _ in range(100):
    d = calculate_delta(d1, d2)

end = datetime.now()

print((end - start) / 100)
print(d1.people['/bab'])

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