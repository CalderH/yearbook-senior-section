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
        main_branch_id = convert_id(start_id, ID.b)

        self.data = JSONDict('database', database_template, {})

        self.data.root = base_version_id
        self.data.branches = {main_branch_id: {}}
        main_branch = self.data.branches[main_branch_id]
        main_branch.name = 'main'
        main_branch.start = base_version_id
        main_branch.end = base_version_id
        self.data.working_branch = main_branch_id

        self.data.views = {}

        self.data.next_version_id = next_id(base_version_id)
        self.data.next_branch_id = next_id(main_branch_id)

        self.data.versions = {base_version_id: {}}
        base_version = self.data.versions[base_version_id]
        base_version.message = 'Base'
        base_version.branch = main_branch_id

        self.save()
    
    def _next_version_id(self):
        output = self.data.next_version_id
        self.data.next_version_id = next_id(output)
        return output

    def _next_branch_id(self):
        output = self.data.next_branch_id
        self.data.next_branch_id = next_id(output)
        return output

    def branch(self, branch_id):
        if branch_id in self.data.branches:
            return self.data.branches[branch_id]
        else:
            raise YBDBException(f'There is no branch with id {branch_id}')
    
    def version(self, version_id):
        if version_id in self.data.versions:
            return self.data.versions[version_id]
        else:
            raise YBDBException(f'There is no branch with id {version_id}')
    
    def load(self):
        with open(self.path) as file:
            self.data = JSONDict('database', database_template, json.load(file))
    
    def save(self):
        with open(self.path, 'w') as file:
            json.dump(self.data._data, file, indent=4)
    
    def check_well_formed(self):
        # TODO
        pass
    
    def commit(self, branch_id):
        branch = self.branch(branch_id)
        
        current_version_id = branch.end
        current_version = self.version(current_version_id)
        if current_version.change is not None and current_version.change.unchecked is not None:
            raise YBDBException('Cannot commit a version with unchecked edits')
        
        new_version_id = self._next_version_id()
        
        self.data.versions[new_version_id] = {}
        new_version = self.data.versions[new_version_id]
        new_version.branch = branch_id
        current_version.next = new_version_id
        new_version.previous = current_version_id
        branch.end = new_version_id

        self.save()
    
    def change_open_version(self, deltas, branch_id, unchecked=None):
        branch = self.branch(branch_id)
        version = self.version(branch.end)

        if 'change' not in version:
            version.change = {}
        version.change.deltas = deltas
        if unchecked is not None:
            version.change.unchecked = unchecked

        self.save()

    def new_branch(self, version_id, name):
        start_version = self.version(version_id)
        new_branch_id = self._next_branch_id()
        self.data.branches[new_branch_id] = {}
        new_branch = self.branch(new_branch_id)
        new_branch.name = name
        new_branch.parent = start_version.branch

        new_version_id = self._next_version_id()
        self.data.versions[new_version_id] = {}
        new_version = self.version(new_version_id)
        new_version.previous = version_id
        new_version.branch = new_branch_id

        new_branch.start = version_id
        new_branch.end = new_version_id
        new_branch.open = True

        start_version.branches_out.append(new_branch_id)

        self.save()
    
    def merge_branches(self, destination_branch_id, source_version_id,
                       default_instructions, record_instructions):
        destination_branch = self.branch(destination_branch_id)
        current_version_id = destination_branch.end
        current_version = self.version(current_version_id)

        if current_version.change is not None:
            raise YBDBException('Cannot merge to a branch with uncommitted changes')
        
        self.version(source_version_id)

        current_version.merge = {}
        merge = current_version.merge
        merge.source = source_version_id
        merge.default = default_instructions
        merge.records = record_instructions

        self.save()
