import json
from json_interface import *
from yearbook_setup import core_path
from id_tools import *


with open(core_path('database template')) as file:
    database_template = json.load(file)


class YBDBException(Exception):
    pass


class Database:
    def __init__(self, path):
        self.path = path
        self.data = None
    
    def setup(self):
        root_commit_id = convert_id(start_id, ID.c)
        main_branch_id = convert_id(start_id, ID.b)
        self.data = JSONDict('database', database_template, {})
        self.data.root = root_commit_id
        self.data.branches = {main_branch_id: {}}
        main_branch = self.data.branches[main_branch_id]
        main_branch.name = 'main'
        main_branch.start = root_commit_id
        main_branch.end = root_commit_id
        main_branch.open = True
        self.data.views = {}
        self.data.working_branch = main_branch_id
        self.data.next_commit_id = next_id(root_commit_id)
        self.data.next_branch_id = next_id(main_branch_id)
        self.data.commits = {root_commit_id: {}}
        initial_commit = self.data.commits[root_commit_id]
        initial_commit.message = 'Initial commit'
        initial_commit.branch = main_branch_id
        initial_commit.records = {}
        self.save()
    
    def load(self):
        with open(self.path) as file:
            self.data = JSONDict('database', database_template, json.load(file))
    
    def save(self):
        with open(self.path, 'w') as file:
            json.dump(self.data._data, file, indent=4)
    
    def check_well_formed(self):
        # TODO
        pass

    def update_open_change(self, deltas, branch=None, unchecked=None):
        if branch is None:
            branch = self.data.working_branch
        branch_info = self.data.branches[branch]
        if not branch_info.open:
            raise YBDBException('Attempted to update the deltas on a committed change')
        change = self.data.changes[branch_info.end]
        change.deltas = deltas
        if unchecked is not None:
            change.unchecked = unchecked
        self.save()
    
    def commit_change(self, branch=None):
        if branch is None:
            branch = self.data.working_branch
        branch_info = self.data.branches[branch]
        if not branch_info.open:
            raise YBDBException('Attempted to commit a change that is already committed')
        
        current_change_id = branch_info.end
        new_change_id = self.data.next_change_id
        current_change = self.data.changes[current_change_id]
        if current_change.unchecked is not None:
            raise YBDBException('Cannot commit a change with unchecked edits')
        
        self.data.changes[new_change_id] = {}
        new_change = self.data.changes[new_change_id]
        new_change.branch = branch
        new_change.deltas = {}
        current_change.next = new_change_id
        new_change.previous = current_change_id
        branch_info.end = new_change_id

        self.data.next_change_id = next_id(new_change_id)

        self.save()

        
