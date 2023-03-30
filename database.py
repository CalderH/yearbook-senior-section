import json
from json_interface import *
from yearbook_setup import core_path
from id_tools import *
from typing import Dict, List, Tuple, NewType
from enum import Enum


Record = NewType('Record', JSONDict)
Version = NewType('Version', JSONDict)
Branch = NewType('Branch', JSONDict)

RecordID = NewType('RecordID', ID)
VersionID = NewType('VersionID', ID)
BranchID = NewType('BranchID', ID)
ViewID = NewType('ViewID', ID)


class VersionType(Enum):
    change = 0
    merge = 1
    revision = 2


with open(core_path('database template')) as file:
    database_template: dict = json.load(file)


class YBDBException(Exception):
    pass


class Database:
    def __init__(self, path: Optional[str] = None, data: Optional[dict] = None):
        self.path = path

        if data is None:
            if path is None:
                self.data = JSONDict('database', database_template, {})
                self.setup()
            else:
                self.data = None
        else:
            self.data = JSONDict('database', database_template, data)
    
    def load(self) -> None:
        """Load the data from the JSON file
        
        Anytime you create a Database object based on a file, you must next call eiter load or setup.
        """

        if self.path is None:
            return
        with open(self.path) as file:
            self.data = JSONDict('database', database_template, json.load(file))
    
    def save(self) -> None:
        """Save this object's data to the JSON file"""

        if self.path is None:
            return
        with open(self.path, 'w') as file:
            json.dump(self.data._data, file, indent=4)
    
    def setup(self) -> None:
        """Create all the fields of an initial, empty database
        
        Anytime you create a Database object based on a file, you must next call eiter load or setup.
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

    def _version_type(version: Version) -> Optional[VersionType]:
        """Returns an enum representing the type of a version, or None if the version has no type"""

        type_dict = {'change': VersionType.change, 'merge': VersionType.merge, 'revision': VersionType.revision}
        included_types = [version_type for version_type in type_dict if version[version_type] is not None]
        if len(included_types) > 1:
            raise YBDBException('Version has multiple types')
        elif included_types == []:
            return None
        else:
            return type_dict[included_types[0]]

    def _get_branch(self, branch_id: BranchID) -> Branch:
        """Get the branch with a given ID, or error if there is no such branch"""

        if branch_id in self.data.branches:
            return self.data.branches[branch_id]
        else:
            raise YBDBException(f'There is no branch with id {branch_id}')
    
    def _get_version(self, version_id: VersionID) -> Version:
        """Get the version with a given ID, or error if there is no such branch"""

        if version_id in self.data.versions:
            return self.data.versions[version_id]
        else:
            raise YBDBException(f'There is no version with id {version_id}')
    
    def _to_version_id(self, id: ID, allow_open = True) -> VersionID:
        is_branch = id_type(id) == IDType.branch

        if is_branch:
            version_id = self._get_branch(id).end
        else:
            version_id = id

        if (not allow_open) and Database._is_open(version := self._get_version(version_id)):
            if is_branch:
                if version.previous is not None:
                    return version.previous
                else:
                    raise YBDBException('There is no committed version')
            else:
                raise YBDBException('Can\'t convert an open version to a closed version')
        else:
            return version_id
    
    def _make_new_version(self) -> Tuple[VersionID, Version]:
        "Create a new empty version, and return the verison's ID and version itself"

        id = self._next_version_id()
        self.data.versions[id] = {}
        return id, self.data.versions[id]

    def _is_open(version: Version) -> bool:
        return version.next is None
    
    def check_well_formed(self):
        # TODO
        pass

    def _trace_back(self, version_id: VersionID, include_revisions=False) -> Tuple[List[VersionID], Dict[VersionID, VersionID]]:
        ancestors = []
        edge = [version_id]
        revisions: Dict[VersionID, VersionID] = {}

        open_version = Database._is_open(self._get_version(version_id))

        while edge != []:
            new_edge = []

            for edge_version_id in edge:
                edge_version = self._get_version(edge_version_id)
                edge_version_type = Database._version_type(edge_version)
                
                if edge_version_type == VersionType.revision:
                    if include_revisions and edge_version_id not in ancestors:
                        ancestors.append(edge_version_id)

                    if open_version:
                        selection = self._to_version_id(edge_version.revision.current, allow_open=False)
                    elif edge_version_id in revisions:
                        selection = revisions[edge_version_id]
                    else:
                        selection = edge_version.revision.original
                    
                    if edge_version_id not in revisions:
                        revisions[edge_version_id] = selection

                    new_edge.append(selection)
                else:
                    if edge_version_id not in ancestors:
                        ancestors.append(edge_version_id)

                    if edge_version.previous is not None:                    
                        previous_id = edge_version.previous
                        new_edge.append(previous_id)

                        if edge_version_type == VersionType.merge:
                            new_edge.append(edge_version.merge.tributary)

                        if not open_version and edge_version_type in [VersionType.change, VersionType.merge]:
                            if edge_version_type == VersionType.change:
                                edge_version_revision_changes = edge_version.change.revision_changes
                            else:
                                edge_version_revision_changes = edge_version.merge.revision_changes
                        
                            if edge_version_revision_changes is not None:
                                for revision_id, selection in edge_version_revision_changes.items():
                                    if revision_id not in revisions:
                                        revisions[revision_id] = selection

            edge = new_edge

        assert(self.data.root in ancestors)
        return ancestors, revisions

    def _ancestry(self, version_id: VersionID, include_revisions=False) -> List[VersionID]:
        return self._trace_back(version_id, include_revisions=include_revisions)[0]

    def _revision_state(self, version_id: VersionID) -> Dict[VersionID, VersionID]:
        return self._trace_back(version_id)[1]
    
    def _find_LCA(self, v1_id: VersionID, v2_id: VersionID) -> VersionID:
        """Finds the latest common ancestor of two versions."""

        v1_ancestors = self._ancestry(v1_id)
        v2_ancestors = self._ancestry(v2_id)
        for ancestor_id in v1_ancestors:
            if ancestor_id in v2_ancestors:
                return ancestor_id
        
        raise YBDBException(f'Unable to find LCA of {v1_id} and {v2_id}')

    def root(self) -> VersionID:
        return self.data.root
    
    def main_branch(self) -> BranchID:
        return self._get_version(self.data.root).branch

    def commit(self, branch_id: BranchID) -> VersionID:
        """Commit the changes that have been made to a branch.
        
        This creates a new blank version at the end of the branch, so the previous end version cannot be edited anymore.
        If the end version has any unchecked edits, raises an error.
        """

        branch = self._get_branch(branch_id)
        
        current_version_id = branch.end
        current_version = self._get_version(current_version_id)

        test = current_version_id == 'v,ci'

        current_version_type = Database._version_type(current_version)
        assert(current_version_type in [VersionType.change, None])

        if current_version_type == VersionType.change and current_version.change.unchecked is not None:
            raise YBDBException('Cannot commit a version with unchecked edits')

        if current_version.previous is not None:
            revisions = self._revision_state(current_version_id)
            previous_revisions = self._revision_state(current_version.previous)
            revisions_have_changed = revisions != previous_revisions
        else:
            revisions_have_changed = False

        if not(current_version_type == VersionType.change or revisions_have_changed):
            # If nothing has changed, don't create a new version
            return
        
        if current_version_type is None and revisions_have_changed:
            current_version.change = {}
        
        if revisions_have_changed:
            revision_changes = {}
            for revision_id in revisions:
                if revision_id not in previous_revisions or revisions[revision_id] != previous_revisions[revision_id]:
                    revision_changes[revision_id] = revisions[revision_id]
            current_version.change.revision_changes = revision_changes
        
        new_version_id, new_version = self._make_new_version()
        new_version.branch = branch_id
        current_version.next = new_version_id
        new_version.previous = current_version_id
        branch.end = new_version_id

        self.save()
        return current_version_id
    
    def update(self, branch_id: BranchID, deltas: Record, unchecked: Optional[Dict[RecordID, List[str]]] = None) -> None:
        """Incorporates edits to the version at the end of a branch.
        
        This *replaces* the previous deltas with new deltas, rather than adding onto the previous deltas.
        """

        version = self._get_version(self._to_version_id(branch_id))

        version_type = Database._version_type(version)
        if version_type not in [VersionType.change, None]:
            raise YBDBException('Cannot make edits to a merge or revision version')

        if version.change is None:
            # If the open version has not had any edits yet, need to mark that this version is a change rather than a merge
            version.change = {}
        version.change.deltas = deltas
        if unchecked is not None:
            version.change.unchecked = unchecked

        self.save()

    def new_branch(self, version_id: VersionID, branch_name: str) -> BranchID:
        """Creates a new branch starting at a given version."""

        start_version = self._get_version(version_id)
        if Database._is_open(start_version):
            raise YBDBException('Cannot make a branch from an open version')

        new_branch_id = self._next_branch_id()
        self.data.branches[new_branch_id] = {}
        new_branch = self._get_branch(new_branch_id)
        new_branch.name = branch_name
        new_branch.parent = start_version.branch

        new_version_id, new_version = self._make_new_version()
        new_version.previous = version_id
        new_version.branch = new_branch_id

        new_branch.start = new_version_id
        new_branch.end = new_version_id

        if start_version.branches_out is None:
            start_version.branches_out = []
        start_version.branches_out.append(new_branch_id)

        self.save()
        return new_branch_id
    
    def merge(self, primary_branch_id: BranchID, tributary_version_id: VersionID,
                       default_instructions: dict, record_instructions: dict) -> VersionID:
        """Merges a given version into the end of a given branch."""
        
        primary_branch = self._get_branch(primary_branch_id)
        merge_version_id = primary_branch.end
        merge_version = self._get_version(merge_version_id)

        merge_version_type = Database._version_type(merge_version)
        assert(merge_version_type in [VersionType.change, None])
        if merge_version_type is not None:
            raise YBDBException('Cannot merge to a branch with uncommitted changes')
        
        assert(merge_version.previous is not None)
        primary_version_id = merge_version.previous

        tributary_version = self._get_version(tributary_version_id)
        if Database._is_open(tributary_version):
            raise YBDBException('Cannot merge a version with uncommitted changes')

        primary_revision_state = self._revision_state(primary_version_id)
        tributary_revision_state = self._revision_state(tributary_version_id)
        merge_revision_state = self._revision_state(merge_version_id)

        revision_changes = {}
        print(primary_revision_state)
        print(tributary_revision_state)
        print(merge_revision_state)
        for revision_id, current_selection in merge_revision_state.items():
            if    (revision_id not in primary_revision_state and revision_id not in tributary_revision_state) \
               or revision_id in primary_revision_state and current_selection != primary_revision_state[revision_id] \
               or revision_id in tributary_revision_state and current_selection != tributary_revision_state[revision_id]:
                revision_changes[revision_id] = current_selection

        merge_version.merge = {}
        merge_info = merge_version.merge
        merge_info.tributary = tributary_version_id
        merge_info.default = default_instructions
        merge_info.records = record_instructions
        if revision_changes != {}:
            merge_info.revision_changes = revision_changes

        if tributary_version.merged_to is None:
            tributary_version.merged_to = []
        tributary_version.merged_to.append(merge_version_id)

        new_version_id, new_version = self._make_new_version()
        merge_version.next = new_version_id
        new_version.previous = merge_version_id
        new_version.branch = primary_branch_id
        primary_branch.end = new_version_id

        self.save()
        return merge_version_id

    def setup_revision(self, output_id: VersionID, primary: bool = True) -> VersionID:
        """Creates a new revision version before a given version.
        
        output_id: the version that the revision will go into
        if that version is a merge, use the primary field to indicate whether this revision affects the primary input (True) or the tributary input (False)
        """

        output_version = self._get_version(output_id)
        if Database._is_open(output_version):
            raise YBDBException('Cannot create a revision before an uncommitted version')

        if output_version.merge and not primary:
            input_id = output_version.merge.tributary
        else:
            input_id = output_version.previous
        input_version = self._get_version(input_id)

        revision_id, revision_version = self._make_new_version()

        input_version.next = revision_id
        output_version.previous = revision_id
        revision_version.previous = input_id
        revision_version.next = output_id

        revision_version.revision = {}
        revision_version.revision.current = input_id
        revision_version.revision.original = input_id

        self.save()
        return revision_id

    def revise(self, revision_id: VersionID, new_id: ID) -> None:
        new_version_id = self._to_version_id(new_id)
        
        if revision_id in self._ancestry(new_version_id, include_revisions=True):
            raise YBDBException('Cannot make a revision select a version downstream of the revision')
        
        revision_version = self._get_version(revision_id)
        if Database._version_type(revision_version) != VersionType.revision:
            raise YBDBException('Cannot revise a non-revision version')
        revision_version.revision.current = new_id
