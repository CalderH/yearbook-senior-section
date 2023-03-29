import unittest
from database import Database


class TestDB(unittest.TestCase):
    def test_create_db(self):
        db = Database()
        db.data.print()




if __name__ == '__main__':
    unittest.main()