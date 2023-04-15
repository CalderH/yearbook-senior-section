from abc import ABC, abstractmethod
from typing import Optional, Set
import database
from database import Database, YBDBException
import json_interface


class View(ABC):
    def __init__(self, db: Database):
        self.db: Database = db
    
    @abstractmethod
    def __getitem__(self, name) -> database.Record:
        ...


class AtomicView(View):
    def __init__(self, db: Database, version_id: Database.VersionID):
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
    
    @abstractmethod
    def av(self) -> AtomicView:
        ...
    
    def __getitem__(self, name):
        return self.av()[name]


class ClosedView(AtomicView):
    def __init__(self, db: Database, version_id: database.VersionID):
        if db._is_open(version_id):
            raise YBDBException('Cannot input an open version id to a ClosedVersionView')
        super().__init__(db, version_id)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        self._state.make_static()


class OpenView(AtomicView):
    def __init__(self, db: Database, version_id: Database.VersionID):
        if not db._is_open(version_id):
            raise YBDBException('Cannot input a closed version id to an OpenVersionView')
        super().__init__(db, version_id)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        revisions = self.db._revision_state(self.version_id).keys()
        # self.affecting_versions = {self.version_id} | revisions
    
    def sync_to_db(self) -> None:
        ...


class OpenChangeView(OpenView):
    def __init__(self, db: Database, version_id: Database.VersionID):
        super().__init__(db, version_id)

    def sync_from_db(self) -> None:
        super().sync_from_db()
        previous_version_id = self.db._get_version(self.version_id).previous
        current_revision_state = self.db._revision_state(self.version_id)
        self._previous_state = self.db.compute_state(previous_version_id, revision_state=current_revision_state)

    def sync_to_db(self) -> None:
        delta = json_interface.calculate_delta(self._previous_state, self._state)
        self.db.update(self.version_id, delta)
        self.db.sync_from_view(self)
    
    def __setitem__(self, key, value):
        self._state[key] = value
    
    def __delitem__(self, key):
        del self._state[key]


class OpenMergeView(OpenView):
    def __init__(self, db: Database, version_id: Database.VersionID):
        super().__init__(db, version_id)
    
    def sync_from_db(self) -> None:
        super().sync_from_db()
        ...
    
    # def set
