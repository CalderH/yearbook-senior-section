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
        base_version_id = convert_id(start_id, ID.v)
        end_version_id = next_id(base_version_id)
        main_branch_id = convert_id(start_id, ID.b)

        self.data = JSONDict('database', database_template, {})

        self.data.root = base_version_id
        self.data.branches = {main_branch_id: {}}
        main_branch = self.data.branches[main_branch_id]
        main_branch.name = 'main'
        main_branch.start = base_version_id
        main_branch.end = end_version_id
        main_branch.open = True
        self.data.working_branch = main_branch_id

        self.data.views = {}

        self.data.next_version_id = next_id(end_version_id)
        self.data.next_branch_id = next_id(main_branch_id)

        self.data.versions = {base_version_id: {}, end_version_id: {}}
        base_version = self.data.versions[base_version_id]
        base_version.message = 'Base'
        base_version.branch = main_branch_id
        base_version.next = end_version_id

        end_version = self.data.versions[end_version_id]
        end_version.branch = main_branch_id
        end_version.previous = base_version_id
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
    
    def commit_version(self, branch_id=None):
        if branch_id is None:
            branch_id = self.data.working_branch
        branch = self.data.branches[branch_id]
        if not branch.open:
            raise YBDBException('Attempted to commit to a closed branch')
        
        current_version_id = branch.end
        new_version_id = self.data.next_version_id
        current_version = self.data.versions[current_version_id]
        if current_version.change is not None and current_version.change.unchecked is not None:
            raise YBDBException('Cannot commit a version with unchecked edits')
        
        self.data.versions[new_version_id] = {}
        new_version = self.data.versions[new_version_id]
        new_version.branch = branch_id
        current_version.next = new_version_id
        new_version.previous = current_version_id
        branch.end = new_version_id

        self.data.next_version_id = next_id(new_version_id)

        self.save()
    
    def change_open_version(self, deltas, branch_id=None, unchecked=None):
        if branch_id is None:
            branch_id = self.data.working_branch
        branch = self.data.branches[branch_id]
        if not branch.open:
            raise YBDBException('Attempted to update the deltas on a committed version')
        version = self.data.versions[branch.end]
        if 'change' not in version:
            version.change = {}
        version.change.deltas = deltas
        if unchecked is not None:
            version.change.unchecked = unchecked
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

        new_branch.end = new_version_id
        new_branch.open = True

        start_version.branches_out.append(new_branch_id)
        
        self.data.next_version_id = next_id(self.data.next_version_id)
        self.data.next_branch_id = next_id(self.data.next_branch_id)
    
    def merge_branches(self, primary_id, secondary_ids):
        pass
