import unittest
from database import Database


class TestDB(unittest.TestCase):
    # def test_create_db(self):
    #     db = Database()
    #     db.data.print()

    def test_revisions(self):
        db = Database()
        db.setup()

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

        self.assertEqual(db._ancestry('v,bo'), ['v,bo', 'v,be', 'v,ba'])
        self.assertEqual(db._ancestry('v,bu'), ['v,bu', 'v,bo', 'v,bi', 'v,ba'])
        self.assertEqual(db._ancestry('v,ci'), ['v,ci', 'v,bu', 'v,bo', 'v,ba'])
    
    def test_merge(self):
        db = Database()
        db.setup()

        db.new_branch('v,ba', 'branch 2')
        db.update('b,ba', {})
        db.commit('b,ba')
        db.update('b,be', {})
        db.commit('b,be')
        db.merge('b,ba', 'v,bi', {}, {})

        self.assertEqual(db._ancestry('v,ca'), ['v,ca', 'v,bo', 'v,be', 'v,bi', 'v,ba'])


if __name__ == '__main__':
    unittest.main()