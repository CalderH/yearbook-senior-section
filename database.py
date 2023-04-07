Database = None
VersionID = None
BranchID = None

import json
from json_interface import *
from yearbook_setup import core_path, construct_path, PS
import ids
from typing import Dict, List, Tuple, NewType
from enum import Enum, StrEnum
import view
import os
import datetime

Record = NewType('Record', JSONDict)
Version = NewType('Version', JSONDict)
Branch = NewType('Branch', JSONDict)
DBState = NewType('DBState', JSONDict)

RecordID = NewType('RecordID', ids.ID)
VersionID = NewType('VersionID', ids.ID)
BranchID = NewType('BranchID', ids.ID)
ViewID = NewType('ViewID', ids.ID)


class VersionType(Enum):
    change = 0
    merge = 1
    revision = 2
    root = 3


class YBDBException(Exception):
    pass


class Database:
    def __init__(self, path: Optional[str], record_template: Optional[dict] = None):
        self.path = path

        with open(core_path('version template')) as file:
            self._version_template: dict = json.load(file)
        with open(core_path('branch template')) as file:
            self._branch_template: dict = json.load(file)
        with open(core_path('view template')) as file:
            self._view_template: dict = json.load(file)

        with open(core_path('id info template')) as file:
            self._id_info_template: dict = json.load(file)

        self._versions = JSONDict('versions', {'': self._version_template}, {})
        self._branches = JSONDict('versions', {'': self._branch_template}, {})
        self._views = JSONDict('versions', {'': self._view_template}, {})
        
        self._id_info = JSONDict('id info', self._id_info_template, {})

        self.view_objects: List[view.EditableVersionView] = []

        self._state_template = {"": record_template}
    
    def _database_path(self, key: str, *args: List[str]) -> str:
        return construct_path(self.path, (PS.core, key), *args)
    
    def load(self) -> None:
        """Load the data from the database directory
        
        Anytime you create a Database object based on a file, you must next call eiter load or setup.
        """

        def load_dir_to_attr(database_dir_key, thing_template, thing_name, attr):
            for file_info in os.scandir(self._database_path(database_dir_key)):
                if not file_info.is_file():
                    continue
                filename = file_info.name
                root, extension = os.path.splitext(filename)
                if extension != '.json':
                    continue
                with open(self._database_path(database_dir_key, filename)) as file:
                    thing_data = json.load(file)
                try:
                    JSONDict('', thing_template, thing_data)
                except:
                    continue
                id = thing_data['id']
                if id != root:
                    raise Exception(f'Encountered a {thing_name} whose filename {root} is different from its id {id}')
                attr[id] = thing_data
        
        with open(self._database_path('id info')) as file:
            self._id_info.set_data(json.load(file))
        load_dir_to_attr('versions', self._version_template, 'version', self._versions)
        load_dir_to_attr('branches', self._branch_template, 'branch', self._branches)
        load_dir_to_attr('views', self._view_template, 'view', self._views)
        
    def save(self) -> None:
        """Save this object's data to the database"""

        if self.path is None:
            return
        
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        
        def save_attr_to_dir(database_dir_key, thing_template, attr):
            if not os.path.exists(self._database_path(database_dir_key)):
                os.mkdir(self._database_path(database_dir_key))
            
            for file_info in os.scandir(self._database_path(database_dir_key)):
                if not file_info.is_file():
                    continue
                filename = file_info.name
                extension = os.path.splitext(filename)[1]
                if extension != '.json':
                    continue
                file_path = self._database_path(database_dir_key, filename)
                with open(file_path) as file:
                    thing_data = json.load(file)
                try:
                    JSONDict('', thing_template, thing_data)
                except:
                    continue
                os.remove(file_path)
            
            for id, value in attr.items():
                with open(self._database_path(database_dir_key, f'{id}.json'), 'w') as file:
                    json.dump(value._template_order(), file, indent=4)
        
        with open(self._database_path('id info'), 'w') as file:
            json.dump(self._id_info._template_order(), file, indent=4)
        save_attr_to_dir('versions', self._version_template, self._versions)
        save_attr_to_dir('branches', self._branch_template, self._branches)
        save_attr_to_dir('views', self._view_template, self._views)
    
    @staticmethod
    def _timestamp():
        return datetime.datetime.now(datetime.timezone.utc).timestamp()

    def setup(self, user_str: Optional[str] = None) -> None:
        """Create all the fields of an initial, empty database
        
        Anytime you create a Database object based on a file, you must next call either load or setup.
        """

        if user_str is None:
            user_str = ''
        self._id_info.user = user_str
        self._id_info.next_record_id = ids.compose_id(ids.IDType.record, user_str, ids.start_sequence)
        self._id_info.next_version_id = ids.compose_id(ids.IDType.version, user_str, ids.start_sequence)
        self._id_info.next_branch_id = ids.compose_id(ids.IDType.branch, user_str, ids.start_sequence)
        self._id_info.next_view_id = ids.compose_id(ids.IDType.view, user_str, ids.start_sequence)

        self._branches[ids.trunk_branch_id] = {}
        main_branch = self._branches[ids.trunk_branch_id]
        main_branch.id = ids.trunk_branch_id
        main_branch.name = 'trunk'
        main_branch.start = ids.root_version_id

        self._versions[ids.root_version_id] = {}
        root_version = self._get_version(ids.root_version_id)
        root_version.id = ids.root_version_id
        root_version.timestamp = self._timestamp()
        root_version.message = 'root'
        root_version.branch = ids.trunk_branch_id
        root_version.root = True

        end_version_id, end_version = self._make_new_version()
        root_version.next = end_version_id
        end_version.previous = ids.root_version_id
        end_version.branch = ids.trunk_branch_id
        main_branch.end = end_version_id

        self.save()
    
    def sync_from_view(self, view: view.EditableVersionView) -> None:
        changed_version = view.version_id
        for other_view in self.view_objects:
            if other_view is view:
                continue
            if changed_version in other_view.affecting_versions:
                other_view.sync_from_db()
    
    def _next_record_id(self) -> RecordID:
        """Get a new unique record ID and increment the record ID counter"""

        output = self._id_info.next_record_id
        self._id_info.next_record_id = ids.next_id(output)
        return output

    def _next_version_id(self) -> VersionID:
        """Get a new unique version ID and increment the version ID counter"""

        output = self._id_info.next_version_id
        self._id_info.next_version_id = ids.next_id(output)
        return output

    def _next_branch_id(self) -> BranchID:
        """Get a new unique branch ID and increment the branch ID counter"""

        output = self._id_info.next_branch_id
        self._id_info.next_branch_id = ids.next_id(output)
        return output
    
    def _next_view_id(self) -> ViewID:
        """Get a new unique view ID and increment the view ID counter"""

        output = self._id_info.next_view_id
        self._id_info.next_view_id = ids.next_id(output)
        return output

    @staticmethod
    def _version_type(version: Version) -> Optional[VersionType]:
        """Returns an enum representing the type of a version, or None if the version has no type"""

        type_dict = {'change': VersionType.change, 'merge': VersionType.merge, 'revision': VersionType.revision, 'root': VersionType.root}
        included_types = [version_type for version_type in type_dict if version[version_type] is not None]
        if len(included_types) > 1:
            raise YBDBException('Version has multiple types')
        elif included_types == []:
            return None
        else:
            return type_dict[included_types[0]]

    def _get_branch(self, branch_id: BranchID) -> Branch:
        """Get the branch with a given ID, or error if there is no such branch"""

        if branch_id in self._branches:
            return self._branches[branch_id]
        else:
            raise YBDBException(f'There is no branch with id {branch_id}')
    
    def _get_version(self, version_id: VersionID) -> Version:
        """Get the version with a given ID, or error if there is no such branch"""

        if version_id in self._versions:
            return self._versions[version_id]
        else:
            raise YBDBException(f'There is no version with id {version_id}')
    
    def _to_version_id(self, id: ids.ID, allow_open = True) -> VersionID:
        is_branch = ids.id_type(id) == ids.IDType.branch

        if is_branch:
            version_id = self._get_branch(id).end
        else:
            version_id = id

        if (not allow_open) and self._is_open(version := self._get_version(version_id)):
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
        "Create a new empty version, and return the version's ID and the version itself"

        id = self._next_version_id()
        self._versions[id] = {}
        self._versions[id].id = id
        return id, self._versions[id]

    @staticmethod
    def _is_open(version: Version) -> bool:
        return version.next is None
    
    def check_well_formed(self):
        # TODO
        pass

    def _trace_back(self, version_id: VersionID, include_revisions=False) -> Tuple[List[VersionID], Dict[VersionID, VersionID], Dict[VersionID, List[VersionID]]]:
        """Traverses backward through the versions to find every version that contributes to the input version.

        Returns 3 things:
        - ancestors: a list of this version's ancestors
            - Breadth-first order
            - For merges, primary input comes before tributary
            - By default does not include revision versions, but can include them by setting include_revisions to True
        - revisions: a dict indicating which selection is made for each revision in the ancestry
        - graph: a dict representing the relationships among the ancestors
            - Each version is mapped to a list containing its direct parents:
                - Root -> empty list
                - Change -> the one previous version
                - Merge -> the primary and tributary inputs (in that order)
            - By default does not include revision versions, but can include them by setting include_revisions to True
        """

        ancestors: List[VersionID] = []
        revisions: Dict[VersionID, VersionID] = {}
        graph: Dict[VersionID, List[VersionID]] = {}

        edge: List[VersionID] = [version_id]

        open_version = self._is_open(self._get_version(version_id))

        while edge != []:
            new_edge = []

            for edge_version_id in edge:
                edge_version = self._get_version(edge_version_id)
                edge_version_type = self._version_type(edge_version)
                
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
                    if include_revisions:
                        graph[edge_version_id] = [selection]
                else:
                    if edge_version_id not in ancestors:
                        ancestors.append(edge_version_id)

                    if edge_version_type != VersionType.root:
                        parents = []

                        previous_id = edge_version.previous
                        parents.append(previous_id)

                        if edge_version_type == VersionType.merge:
                            parents.append(edge_version.merge.tributary)
                        
                        graph[edge_version_id] = parents
                        new_edge += parents

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

        assert(ids.root_version_id in ancestors)

        if not include_revisions:
            for version_id, parents in graph.items():
                new_parents = []
                for parent_id in parents:
                    if parent_id in revisions:
                        new_parents.append(revisions[parent_id])
                    else:
                        new_parents.append(parent_id)
                graph[version_id] = new_parents

        return ancestors, revisions, graph

    def _ancestry(self, version_id: VersionID, include_revisions=False) -> List[VersionID]:
        return self._trace_back(version_id, include_revisions=include_revisions)[0]

    def _revision_state(self, version_id: VersionID) -> Dict[VersionID, VersionID]:
        return self._trace_back(version_id)[1]

    def _graph(self, version_id: VersionID) -> Dict[VersionID, List[VersionID]]:
        return self._trace_back(version_id)[2]

    def _find_LCA(self, v1_id: VersionID, v2_id: VersionID) -> VersionID:
        """Finds the latest common ancestor of two versions."""

        v1_ancestors = self._ancestry(v1_id)
        v2_ancestors = self._ancestry(v2_id)
        for ancestor_id in v1_ancestors:
            if ancestor_id in v2_ancestors:
                return ancestor_id
        
        raise YBDBException(f'Unable to find LCA of {v1_id} and {v2_id}')

    def commit(self, branch_id: BranchID) -> VersionID:
        """Commit the changes that have been made to a branch.
        
        This creates a new blank version at the end of the branch, so the previous end version cannot be edited anymore.
        If the end version has any unchecked edits, raises an error.
        """

        branch = self._get_branch(branch_id)
        
        current_version_id = branch.end
        current_version = self._get_version(current_version_id)

        current_version_type = self._version_type(current_version)
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
        
        previous_revisions_using = self._get_version(current_version.previous).revisions_using
        previous_revisions_using_copy = previous_revisions_using.copy()
        current_version.revisions_using = []
        for revision_id in previous_revisions_using_copy:
            revision = self._get_version(revision_id)
            if ids.id_type(revision.revision.current) == ids.IDType.branch:
                previous_revisions_using.remove(revision_id)
                current_version.revisions_using.append(revision_id)
            else:
                continue
        if current_version.revisions_using == []:
            del current_version.revisions_using
            
        current_version.timestamp = self._timestamp()
        
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

        version_type = self._version_type(version)
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
        if self._is_open(start_version):
            raise YBDBException('Cannot make a branch from an open version')

        new_branch_id = self._next_branch_id()
        self._branches[new_branch_id] = {}
        new_branch = self._get_branch(new_branch_id)
        new_branch.name = branch_name

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

        merge_version_type = self._version_type(merge_version)
        assert(merge_version_type in [VersionType.change, None])
        if merge_version_type is not None:
            raise YBDBException('Cannot merge to a branch with uncommitted changes')
        
        assert(merge_version.previous is not None)
        primary_version_id = merge_version.previous

        tributary_version = self._get_version(tributary_version_id)
        if self._is_open(tributary_version):
            raise YBDBException('Cannot merge a version with uncommitted changes')

        primary_revision_state = self._revision_state(primary_version_id)
        tributary_revision_state = self._revision_state(tributary_version_id)
        merge_revision_state = self._revision_state(merge_version_id)

        revision_changes = {}
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
        
        previous_revisions_using = self._get_version(merge_version.previous).revisions_using
        previous_revisions_using_copy = previous_revisions_using.copy()
        merge_version.revisions_using = []
        for revision_id in previous_revisions_using_copy:
            revision = self._get_version(revision_id)
            if ids.id_type(revision.revision.current) == ids.IDType.branch:
                previous_revisions_using.remove(revision_id)
                merge_version.revisions_using.append(revision_id)
            else:
                continue
        if merge_version.revisions_using == []:
            del merge_version.revisions_using

        merge_version.timestamp = self._timestamp()

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

    def setup_revision(self, prev_id: VersionID) -> VersionID:
        """Creates a new revision version after a given version.
        
        prev_id: the version that the revision will go after
        returns the id of the resulting revision
        """

        prev_version = self._get_version(prev_id)
        if self._is_open(prev_version):
            raise YBDBException('Cannot create a revision after an uncommitted version')
        
        next_version = self._get_version(prev_version.next)
    
        revision_id, revision_version = self._make_new_version()

        revision_version.branch = prev_version.branch
        revision_version.previous = prev_id
        revision_version.next = prev_version.next
        prev_version.next = revision_id
        next_version.previous = revision_id

        if prev_version.branches_out is not None:
            revision_version.branches_out = prev_version.branches_out
            for branch_id in revision_version.branches_out:
                branch_start_version = self._get_version(self._get_branch(branch_id).start)
                branch_start_version.prev = revision_id
        
        if prev_version.merged_to is not None:
            revision_version.merged_to = prev_version.merged_to
            for merge_version_id in revision_version.merged_to:
                merge_version = self._get_version(merge_version_id)
                merge_version.merge.tributary = revision_id
        
        if prev_version.revisions_using is not None:
            revision_version.revisions_using = prev_version.revisions_using
            for other_revision_id in revision_version.revisions_using:
                other_revision = self._get_version(other_revision_id)
                other_revision.current = revision_id

        revision_version.revision = {}
        revision_version.revision.current = prev_id
        revision_version.revision.original = prev_id

        if prev_version.revisions_using is None:
            prev_version.revisions_using = []
        prev_version.revisions_using.append(revision_id)

        self.save()
        return revision_id

    def revise(self, revision_id: VersionID, new_id: ids.ID) -> None:
        new_version_id = self._to_version_id(new_id, allow_open=False)
        
        if revision_id in self._ancestry(new_version_id, include_revisions=True):
            raise YBDBException('Cannot make a revision select a version downstream of the revision')
        
        revision_version = self._get_version(revision_id)
        if self._version_type(revision_version) != VersionType.revision:
            raise YBDBException('Cannot revise a non-revision version')
        
        old_current = self._get_version(revision_version.revision.current)
        new_current = self._get_version(new_version_id)

        old_current.revisions_using.remove(revision_id)
        if new_current.revisions_using is None:
            new_current.revisions_using = []
        new_current.revisions_using.append(revision_id)

        revision_version.revision.current = new_id

    @staticmethod
    def _compute_merge(primary: DBState, tributary: DBState, lca: DBState, rules: JSONDict) -> DBState:       
        # Giving these strings names so it's easier to know what I'm writing
        class MergeRule(StrEnum):
            inherit = ''
            inherit_prioritizing_field = 'f'
            inherit_prioritizing_record = 'r'
            primary_if_conflict = 'p'
            tributary_if_conflict = 't'
            primary_always = 'p!'
            tributary_always = 't!'
        MR = MergeRule
        explicit_rules = [MR.primary_if_conflict, MR.tributary_if_conflict, MR.primary_always, MR.tributary_always]

        # Used for selecting which version to take from
        class MergeChoice(Enum):
            primary = 0
            tributary = 1
        MC = MergeChoice

        # The logic for selecting which version to take from given which versions have made edits and what rule is used
        def apply_rule(primary_edit: bool, tributary_edit: bool, rule: MergeRule) -> MergeChoice:
            if rule == MR.primary_always:
                return MC.primary
            elif rule == MR.tributary_always:
                return MC.tributary
            elif rule == MR.primary_if_conflict:
                if primary_edit:
                    return MC.primary
                else:
                    return MC.tributary
            elif rule == MR.tributary_if_conflict:
                if tributary_edit:
                    return MC.tributary
                else:
                    return MC.primary
            else:
                raise YBDBException('get_choice must take an explicit rule, not an inherited rule')

        # Create the output db state
        output = primary.new()

        # The rules input will be the merge field of a version. Get the subfields for ease of use:
        default_rule = rules.default.all
        field_rules = rules.default.fields
        inherit_priority = rules.default.inherit_priority
        record_rules = rules.records

        # Figure out what fields have been edited
        primary_deltas = calculate_delta(lca, primary)
        tributary_deltas = calculate_delta(lca, tributary)

        # Build up the resulting version, record by record
        for record_id in primary.keys() | tributary.keys():
            # See which input(s) have made edits to this version since the LCA
            primary_edit = record_id in primary_deltas
            tributary_edit = record_id in tributary_deltas
            
            # Get the values of this record in the inputs
            primary_record = primary[record_id]
            tributary_record = tributary[record_id]

            # First deal with the possibility that this version only exists in one of the two inputs
            # either because it was there in the LCA and one of the inputs deleted it
            # or because it was not in the LCA and one of the inputs created it

            # Figure out what rule to use here
            if record_rules is not None and record_id in record_rules and (r := record_rules[record_id].all) is not None:
                record_general_rule = r
            else:
                record_general_rule = default_rule
            
            # Decide what to do based on which inputs have made edits
            record_choice = apply_rule(primary_edit, tributary_edit, record_general_rule)
            if primary_record == None:
                # If this record is not in the primary input
                if record_choice == MC.tributary:
                    # If we're choosing the tributary version, then just go with that
                    # Don't need to break it down by fields because there are none in the primary to compare it to
                    output[record_id] = tributary[record_id]
                # If we're choosing the primary version, then don't add anything to the output for this record
                continue
            elif tributary_record == None:
                # Same logic as above
                if record_choice == MC.primary:
                    output[record_id] = primary[record_id]
                continue
                
            # At this point we know that the record is in both inputs, so we actually have to compare the edits
                
            # See what edits they have made
            primary_record_delta = {}
            tributary_record_delta = {}
            if record_id in primary_deltas:
                primary_record_delta = primary_deltas[record_id]
            if record_id in tributary_deltas:
                tributary_record_delta = tributary_deltas[record_id]
                
            # Create the record to be added in the output db
            output_record = primary_record.new()
            
            # Now build up the record, field by field
            for field in output_record._template:
                # Get the four rules that are relevant here
                # default_rule: the default rule for the whole merge
                # field_rule: the default rule for this field across all records
                # record_rule: the default rule for all fields of this record
                # record_field_rule: the rule for this specific field of this record

                if field_rules is not None and field in field_rules:
                    field_rule = field_rules[field]
                else:
                    field_rule = MR.inherit

                if record_rules is not None and record_id in record_rules:
                    this_record_rules = record_rules[record_id]

                    if (r := this_record_rules.all) is not None:
                        record_rule = r
                    else:
                        record_rule = MR.inherit
                    
                    if (a := this_record_rules.fields) is not None and (r := a[field]) is not None:
                        record_field_rule = r
                    else:
                        record_field_rule = MR.inherit
                
                # From these four rules, figure out what rule to apply in this case
                if record_field_rule in explicit_rules:
                    rule = record_field_rule
                else:
                    if field_rule in explicit_rules:
                        if record_rule in explicit_rules and field_rule != record_rule:
                            if record_field_rule == MR.inherit_prioritizing_field:
                                rule = field_rule
                            elif record_field_rule == MR.inherit_prioritizing_record:
                                rule = record_rule
                            elif inherit_priority == MR.inherit_prioritizing_field:
                                rule = field_rule
                            else:
                                rule = record_rule
                        else:
                            rule = field_rule
                    else:
                        if record_rule in explicit_rules:
                            rule = record_rule
                        else:
                            rule = default_rule
                
                # See which inputs made edits
                primary_edit = field in primary_record_delta
                tributary_edit = field in tributary_record_delta

                # Figure out which to go with
                record_field_choice = apply_rule(primary_edit, tributary_edit, rule)
                if record_field_choice == MC.primary:
                    output_field = primary_record[field]
                else:
                    output_field = tributary_record[field]
                
                # Set the value in the record
                if output_field is not None:
                    output_record[field] = output_field

            output[record_id] = output_record
        
        return output

    def compute_state(self, id: ids.ID) -> DBState:
        version_id = self._to_version_id(id)
        version = self._get_version(version_id)

        if self._version_type(version) == VersionType.revision:
            raise YBDBException('Cannot compute the state of the database at a revision')

        graph = self._graph(version_id)
        
        calculated_versions: Dict[VersionID, DBState] = {}
        
        while version_id not in calculated_versions:
            remaining_graph = graph.copy()

            for ancestor_id, parent_ids in graph.items():
                if ancestor_id == ids.root_version_id:
                    calculated_versions[ancestor_id] = JSONDict('database state', self._state_template, {})
                    
                    del remaining_graph[ancestor_id]

                elif all(parent_id in calculated_versions for parent_id in parent_ids):
                    ancestor_version = self._get_version(ancestor_id)
                    ancestor_type = self._version_type(ancestor_version)

                    if ancestor_type == VersionType.change:
                        assert(ancestor_version.previous == parent_ids[0])
                        parent_state = calculated_versions[ancestor_version.previous]
                        calculated_versions[ancestor_id] = add_delta(parent_state, ancestor_version.change.deltas)

                    else:
                        assert(ancestor_type == VersionType.merge)
                        primary_id = ancestor_version.previous
                        tributary_id = ancestor_version.merge.tributary
                        assert(parent_ids == [primary_id, tributary_id])

                        primary_state = calculated_versions[primary_id]
                        tributary_state = calculated_versions[tributary_id]
                        lca_id = self._find_LCA(primary_id, tributary_id)
                        lca_state = calculated_versions[lca_id]
                        calculated_versions[ancestor_id] = self._compute_merge(primary_state, tributary_state, lca_state, ancestor_version.merge)
                    
                    del remaining_graph[ancestor_id]
            
            graph = remaining_graph

        return calculated_versions[version_id]

    def print(self):
        if self.path is not None:
            print(f'LOCATION: {self.path}\n')
        print('\nID INFO --------------------')
        self._id_info.print()
        print('\n\nVIEWS --------------------')
        self._views.print()
        print('\n\nBRANCHES --------------------')
        self._branches.print()
        print('\n\nVERSIONS --------------------')
        self._versions.print()