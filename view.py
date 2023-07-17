from abc import ABC, abstractmethod
from typing import Optional, Set
import database
from database import Database, YBDBException
import json_interface
import ids


class View(ABC):
    def __init__(self, db: Database):
        super().__init__()
        self.db: Database = db

    @abstractmethod
    def __getitem__(self, name) -> database.Record:
        ...


class AtomicView(View):
    def __init__(self, db: Database, version_id: database.VersionID):
        super().__init__(db)
        if version_id not in self.db._versions:
            raise YBDBException(f'There is no version with id {version_id}')
        self.version_id: str = version_id
        self.sync_from_db()
    
    def sync_from_db(self) -> None:
        self._state: database.DBState = self.db.compute_state(self.version_id)

    def __getitem__(self, name) -> database.Record:
        return self._state[name]
    
    def __contains__(self, name):
        return name in self._state
    
    def __len__(self):
        return len(self._state)
    
    def __iter__(self):
        return self._state.__iter__()

    def items(self):
        return self._state.items()
    
    def keys(self):
        return self._state.keys()
    
    def values(self):
        return self._state.values()
    
    def process_file(self, cv: 'ContainerView') -> None:
        if cv.has_file:
            self._process_file(cv)
    
    def update_file(self, cv: 'ContainerView') -> None:
        if cv.has_file:
            self._update_file(cv)
    
    def _process_file(self, cv: 'ContainerView') -> None:
        ...
    
    def _update_file(self, cv: 'ContainerView') -> None:
        ...
        

class ContainerView(View):
    def __init__(self, db: Database, file: Optional[str] = None):
        super().__init__(db)
        self.file = file
        self.has_file = self.file is not None
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        self.av = self._get_av()
    
    @abstractmethod
    def _get_av(self) -> AtomicView:
        ...
    
    def __getitem__(self, name):
        return self.av[name]


class ClosedView(AtomicView):
    def __init__(self, db: Database, version_id: database.VersionID):
        if db._is_open(version_id):
            raise YBDBException('Cannot input an open version id to a ClosedView')
        super().__init__(db, version_id)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        self._state.make_static()


class EditableView(AtomicView):
    def sync_to_db(self) -> None:
        self._sync_to_db()
        self.db.sync_from_view(self)

    @abstractmethod
    def _sync_to_db(self) -> None:
        ...


class OpenView(EditableView):
    def __init__(self, db: Database, version_id: database.VersionID):
        if not db._is_open(version_id):
            raise YBDBException('Cannot input a closed version id to an OpenView')
        super().__init__(db, version_id)


class MergeView(AtomicView):
    def __init__(self, db: Database, version_id: database.VersionID):
        if db._version_type(db._get_version(version_id)) != database.VersionType.merge:
            raise YBDBException('Cannot input a non-merge version id to a MergeView')
        super().__init__(db, version_id)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        version = self.db._get_version(self.version_id)
        self.primary = version.previous
        self.tributary = version.merge.tributary
        self.default_rules = version.merge.default
        self.record_rules = version.merge.records


class ClosedChangeView(ClosedView):
    pass


class ClosedMergeView(ClosedView, MergeView):
    def sync_from_db(self):
        super().sync_from_db()
        self.default_rules.make_static()
        self.record_rules.make_static()


class OpenChangeView(OpenView):
    def sync_from_db(self) -> None:
        super().sync_from_db()
        previous_version_id = self.db._get_version(self.version_id).previous
        current_revision_state = self.db._revision_state(self.version_id)
        self._previous_state = self.db.compute_state(previous_version_id, revision_state=current_revision_state)

    def _sync_to_db(self) -> None:
        deltas = json_interface.calculate_delta(self._previous_state, self._state)
        self.db.update(self.version_id, deltas)
    
    def __setitem__(self, key, value):
        self._state[key] = value
    
    def __delitem__(self, key):
        del self._state[key]


class OpenMergeView(OpenView, MergeView):
    def _sync_to_db(self) -> None:
        self.db.edit_merge(self.version_id, self.default_rules, self.record_rules)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        self.default_rules._callback = self.sync_from_db
        self.record_rules._callback = self.sync_from_db


class RevisionView(EditableView):
    def __init__(self, db: Database, version_id: database.VersionID):
        version = db._get_version(version_id)
        if db._version_type(version) != database.VersionType.revision:
            raise YBDBException('Cannot input a non-revision version id to a RevisionView')
        self.original = version.revision.original
        super().__init__(db, version_id)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        self.current = self.db._get_version(self.version_id).current
    
    def _sync_to_db(self) -> None:
        self.db.revise(self.version_id, self.current)
    
    def revise(self, new_id: ids.ID):
        self.current = new_id


class VersionView(ContainerView):
    def __init__(self, db: Database, version_id: database.VersionID, file: Optional[str] = None):
        super().__init__(db, file)
        self.version_id = version_id
    
    def _get_av(self) -> AtomicView:
        version = self.db._get_version(self.version_id)
        is_open = self.db._is_open(version)
        version_type = self.db._version_type(version)
        if version_type == database.VersionType.change:
            if is_open:
                return OpenChangeView(self.db, self.version_id)
            else:
                return ClosedChangeView(self.db, self.version_id)
        elif version_type == database.VersionType.merge:
            if is_open:
                return OpenMergeView(self.db, self.version_id)
            else:
                return ClosedMergeView(self.db, self.version_id)
        elif version_type == database.VersionType.revision:
            return RevisionView(self.db, self.version_id)


class BranchView(ContainerView):
    ...

    