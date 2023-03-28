import json
from json_interface import *
from yearbook_setup import core_path
from id_tools import *
from typing import Dict, List


Record = Annotated[JSONDict, 'record']
Version = Annotated[JSONDict, 'version']
Branch = Annotated[JSONDict, 'branch']

RecordID = Annotated[ID, 'record']
VersionID = Annotated[ID, 'version']
BranchID = Annotated[ID, 'branch']
ViewID = Annotated[ID, 'view']


with open(core_path('database template')) as file:
    database_template: dict = json.load(file)


class YBDBException(Exception):
    pass


class Database:
    def __init__(self, path: str):
        self.path = path
        self.data = None
    
    def load(self) -> NoReturn:
        """Load the data from the JSON file
        
        Anytime you create a Database object, you must next call eiter load or setup.
        """

        with open(self.path) as file:
            self.data = JSONDict('database', database_template, json.load(file))
    
    def save(self) -> NoReturn:
        """Save this object's data to the JSON file"""

        with open(self.path, 'w') as file:
            json.dump(self.data._data, file, indent=4)
    
    def setup(self) -> NoReturn:
        """Create all the fields of an initial, empty database
        
        Anytime you create a Database object, you must next call eiter load or setup.
        """

        self.data = JSONDict('database', database_template, {})

        base_version_id = convert_id(start_id, IDType.version)
        main_branch_id = convert_id(start_id, IDType.branch)

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
        self.data.next_view_id = convert_id(start_id, IDType.view)

        self.data.versions = {base_version_id: {}}
        base_version = self.data.versions[base_version_id]
        base_version.message = 'Base'
        base_version.branch = main_branch_id

        self.save()
    
    def _next_version_id(self) -> VersionID:
        """Get a new unique version ID and increment the version ID counter"""

        output = self.data.next_version_id
        self.data.next_version_id = next_id(output)
        return output

    def _next_branch_id(self) -> BranchID:
        """Get a new unique branch ID and increment the version ID counter"""

        output = self.data.next_branch_id
        self.data.next_branch_id = next_id(output)
        return output
    
    def _next_view_id(self) -> ViewID:
        """Get a new unique view ID and increment the version ID counter"""

        output = self.data.next_view_id
        self.data.next_view_id = next_id(output)
        return output

    def branch(self, branch_id: BranchID) -> Branch:
        """Get the branch with a given ID, or error if there is no such branch"""

        if branch_id in self.data.branches:
            return self.data.branches[branch_id]
        else:
            raise YBDBException(f'There is no branch with id {branch_id}')
    
    def version(self, version_id: VersionID) -> Version:
        """Get the version with a given ID, or error if there is no such branch"""

        if version_id in self.data.versions:
            return self.data.versions[version_id]
        else:
            raise YBDBException(f'There is no branch with id {version_id}')
    
    def check_well_formed(self):
        # TODO
        pass
    
    def commit(self, branch_id: BranchID) -> NoReturn:
        """Commit the changes that have been made to a branch.
        
        This creates a new blank version at the end of the branch, so the previous end version cannot be edited anymore.
        If the end version has any unchecked edits, raises an error.
        """

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
    
    def change_open_version(self, branch_id: BranchID, deltas: Record, unchecked: Optional[Dict[RecordID, List[str]]] = None) -> NoReturn:
        """Incorporates edits to the version at the end of a branch.
        
        This *replaces* the previous deltas with new deltas, rather than adding onto the previous deltas.
        """

        branch = self.branch(branch_id)
        version = self.version(branch.end)

        if 'change' not in version:
            # If the open version has not had any edits yet, need to mark that this version is a change rather than a merge
            version.change = {}
        version.change.deltas = deltas
        if unchecked is not None:
            version.change.unchecked = unchecked

        self.save()

    def new_branch(self, version_id: VersionID, branch_name: str) -> NoReturn:
        """Creates a new branch starting at a given version."""

        start_version = self.version(version_id)
        new_branch_id = self._next_branch_id()
        self.data.branches[new_branch_id] = {}
        new_branch = self.branch(new_branch_id)
        new_branch.name = branch_name
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
    
    def merge_branches(self, primary_branch_id: BranchID, tributary_version_id: VersionID,
                       default_instructions: dict, record_instructions: dict):
        """Merges a given version into the end of a given branch."""
        
        primary_branch = self.branch(primary_branch_id)
        current_version_id = primary_branch.end
        current_version = self.version(current_version_id)

        if current_version.change is not None:
            raise YBDBException('Cannot merge to a branch with uncommitted changes')
        
        self.version(tributary_version_id)

        current_version.merge = {}
        merge = current_version.merge
        merge.tributary = tributary_version_id
        merge.default = default_instructions
        merge.records = record_instructions

        self.save()
