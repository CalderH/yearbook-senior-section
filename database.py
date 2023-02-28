import json
from json_interface import *
from yearbook_setup import core_path
from id_tools import *


with open(core_path('database template')) as file:
    database_template = json.load(file)


class Database:
    def __init__(self, path):
        self.path = path
        self.db = None
    
    def setup(self):
        root_commit_id = convert_id(start_id, ID.c)
        main_branch_id = convert_id(start_id, ID.b)
        self.db = JSONDict('database', database_template, {})
        self.db.root = root_commit_id
        self.db.branches = {main_branch_id: {}}
        main_branch = self.db.branches[main_branch_id]
        main_branch.name = 'main'
        main_branch.start = root_commit_id
        main_branch.end = root_commit_id
        main_branch.open = True
        self.db.views = {}
        self.db.working_branch = main_branch_id
        self.db.next_commit_id = next_id(root_commit_id)
        self.db.next_branch_id = next_id(main_branch_id)
        self.db.commits = {root_commit_id: {}}
        initial_commit = self.db.commits[root_commit_id]
        initial_commit.message = 'Initial commit'
        initial_commit.branch = main_branch_id
        initial_commit.records = {}
        self.save()
    
    def load(self):
        with open(self.path) as file:
            self.db = JSONDict('database', database_template, json.load(file))
    
    def save(self):
        with open(self.path, 'w') as file:
            json.dump(self.db, file, indent=4)
    
    def check_well_formed(self):
        # TODO
        pass
    
    