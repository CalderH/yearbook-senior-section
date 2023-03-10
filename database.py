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

    def update_open_version(self, deltas, branch=None, unchecked=None):
        if branch is None:
            branch = self.data.working_branch
        branch_info = self.data.branches[branch]
        if not branch_info.open:
            raise YBDBException('Attempted to update the deltas on a committed version')
        version = self.data.versions[branch_info.end]
        version.deltas = deltas
        if unchecked is not None:
            version.unchecked = unchecked
        self.save()
    
    def commit_version(self, branch=None):
        if branch is None:
            branch = self.data.working_branch
        branch_info = self.data.branches[branch]
        if not branch_info.open:
            raise YBDBException('Attempted to commit to a closed branch')
        
        current_version_id = branch_info.end
        new_version_id = self.data.next_version_id
        current_version = self.data.versions[current_version_id]
        if current_version.unchecked is not None:
            raise YBDBException('Cannot commit a version with unchecked edits')
        
        self.data.versions[new_version_id] = {}
        new_version = self.data.versions[new_version_id]
        new_version.branch = branch
        new_version.deltas = {}
        current_version.next = new_version_id
        new_version.previous = current_version_id
        branch_info.end = new_version_id

        self.data.next_version_id = next_id(new_version_id)

        self.save()

    def new_branch(self, version_id, name):
        if version_id not in self.data.versions:
            raise YBDBException(f'There is no version with id {version_id}')

        start_version = self.data.versions[version_id]
        new_branch_id = self.data.next_branch_id
        self.data.branches[new_branch_id] = {}
        new_branch = self.data.branches[new_branch_id]
        new_branch.name = name
        new_branch.parent = start_version.branch
        new_branch.start = version_id

        new_version_id = self.data.next_version_id
        self.data.versions[new_version_id] = {}
        new_version = self.data.versions[new_version_id]
        new_version.previous = version_id
        new_version.branch = new_branch_id
        new_version.deltas = {}

        new_branch.end = new_version_id
        new_branch.open = True

        start_version.branches_out.append(new_branch_id)
        
        self.data.next_version_id = next_id(self.data.next_version_id)
        self.data.next_branch_id = next_id(self.data.next_branch_id)
        