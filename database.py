import json
from json_interface import *
from yearbook_setup import core_path
from id_tools import *
from typing import Dict, List, Tuple
from enum import Enum


Record = Annotated[JSONDict, 'record']
Version = Annotated[JSONDict, 'version']
Branch = Annotated[JSONDict, 'branch']

RecordID = Annotated[ID, 'record']
VersionID = Annotated[ID, 'version']
BranchID = Annotated[ID, 'branch']
ViewID = Annotated[ID, 'view']


class VersionType(Enum):
    change = 0
    merge = 1
    revision = 2


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

    def version_type(version: Version) -> Optional[VersionType]:
        """Returns an enum representing the type of a version, or None if the version has no type"""

        type_dict = {'change': VersionType.change, 'merge': VersionType.merge, 'revision': VersionType.revision}
        included_types = [version[version_type] is not None for version_type in type_dict]
        if len(included_types) > 1:
            raise YBDBException('Version has multiple types')
        elif included_types == 0:
            return None
        else:
            return type_dict[included_types[0]]

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
    
    def _make_new_version(self) -> Tuple[VersionID, Version]:
        "Create a new empty version, and return the verison's ID and version itself"

        id = self._next_version_id()
        self.data.versions[id] = {}
        return id, self.data.versions[id]

    def is_open(version: Version) -> bool:
        return version.next is None
    
    def check_well_formed(self):
        # TODO
        pass

    def _ancestry(self, version_id: VersionID) -> List[VersionID]:
        ancestors = []
        edge = [(version_id, {})]

        open_version = Database.is_open(self.version(version_id))

        while edge != []:
            new_edge = []
            for edge_version_id, revisions in edge:
                if edge_version_id not in ancestors:
                    ancestors.append(edge_version_id)

                edge_version = self.version(edge_version_id)
                edge_version_type = Database.version_type(edge_version)
                
                if edge_version_type == VersionType.revision:
                    if open_version:
                        new_edge.append((edge_version.revision.current, revisions))
                    elif edge_version_id in revisions:
                        new_edge.append((revisions[edge_version_id], revisions))
                    else:
                        new_edge.append((edge_version.revision.original, revisions))
                else:
                    previous_id = edge_version.previous
                    if previous_id is not None:
                        for revision_id, choice in edge_version.change.revisions:
                            if revision_id not in revisions:
                                revisions[revision_id] = choice
                        new_edge.append((previous_id, revisions))
                    
                    if edge_version_type == VersionType.merge:
                        new_edge.append((edge_version.merge.tributary, revisions.copy()))
        
        assert(self.data.root in ancestors)
        return ancestors
    
    def _find_LCA(self, v1_id: VersionID, v2_id: VersionID) -> VersionID:
        """Finds the latest common ancestor of two versions."""

        v1_ancestors = self._ancestry(v1_id)
        v2_ancestors = self._ancestry(v2_id)
        for ancestor_id in v1_ancestors:
            if ancestor_id in v2_ancestors:
                return ancestor_id
        
        raise YBDBException(f'Unable to find LCA of {v1_id} and {v2_id}')

    def commit(self, branch_id: BranchID) -> NoReturn:
        """Commit the changes that have been made to a branch.
        
        This creates a new blank version at the end of the branch, so the previous end version cannot be edited anymore.
        If the end version has any unchecked edits, raises an error.
        """

        branch = self.branch(branch_id)
        
        current_version_id = branch.end
        current_version = self.version(current_version_id)

        current_version_type = Database.version_type(current_version)
        if current_version_type != VersionType.change:
            raise YBDBException('Can only commit to a change version')
        if current_version.change.unchecked is not None:
            raise YBDBException('Cannot commit a version with unchecked edits')
        
        revisions = {}
        ancestry = self._ancestry(current_version_id)
        for ancestor_id in ancestry:
            ancestor = self._version(ancestor_id)
            if Database.version_type(ancestor) == VersionType.revision:
                revisions[ancestor_id] = ancestor.current
        current_version.revisions = revisions

        new_version_id, new_version = self._make_new_version()
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

        version_type = Database.version_type(version)
        if version_type not in [VersionType.change, None]:
            raise YBDBException('Cannot make edits to a merge or revision version')

        if version.change is None:
            # If the open version has not had any edits yet, need to mark that this version is a change rather than a merge
            version.change = {}
        version.change.deltas = deltas
        if unchecked is not None:
            version.change.unchecked = unchecked

        self.save()

    def new_branch(self, version_id: VersionID, branch_name: str) -> NoReturn:
        """Creates a new branch starting at a given version."""

        start_version = self.version(version_id)
        if Database.is_open(start_version):
            raise YBDBException('Cannot make a branch from an open version')

        new_branch_id = self._next_branch_id()
        self.data.branches[new_branch_id] = {}
        new_branch = self.branch(new_branch_id)
        new_branch.name = branch_name
        new_branch.parent = start_version.branch

        new_version_id, new_version = self._make_new_version()
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

        current_version_type = Database.version_type(current_version)
        if current_version_type == VersionType.change:
            raise YBDBException('Cannot merge to a branch with uncommitted changes')
        if current_version_type == VersionType.revision:
            raise YBDBException('Cannot merge to a revision')
        assert(current_version_type is None)
        
        tributary = self.version(tributary_version_id)
        tributary.merged_to.append(current_version_id)

        current_version.merge = {}
        merge = current_version.merge
        merge.tributary = tributary_version_id
        merge.default = default_instructions
        merge.records = record_instructions

        new_version_id, new_version = self._make_new_version()
        current_version.next = new_version_id
        new_version.previous = current_version
        new_version.branch = primary_branch_id

        self.save()

    def create_revision(self, output_id: VersionID, primary: Optional[bool] = True) -> NoReturn:
        """Creates a new revision version before a given version.
        
        output_id: the version that the revision will go into
        if that version is a merge, use the primary field to indicate whether this revision affects the primary input (True) or the tributary input (False)
        """

        output_version = self.version(output_id)

        if output_version.merge and not primary:
            input_id = output_version.merge.tributary
        else:
            input_id = output_version.previous
        input_version = self.version(input_id)

        revision_id, revision_version = self._make_new_version()

        input_version.next = revision_id
        output_version.previous = revision_id
        revision_version.prev = input_id
        revision_version.next = output_id

        revision_version.revision.current = input_id
        revision_version.revision.original = input_id

    def change_revision(self, revision_id: VersionID, new_id: ID) -> NoReturn:
        if decompose_id(new_id)[1] == IDType.branch:
            new_version_id = self.branch(new_id).end
        else:
            new_version_id = new_id
        
        if revision_id in self._ancestors(new_version_id):
            raise YBDBException('Cannot make a revision select a version downstream of the revision')
        
        revision = self.version(revision_id)
        revision.current = new_id
