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
        self._state: database.DBState = self.db.compute_state(self.version_id)
    
    def __getitem__(self, name) -> database.Record:
        return self._state[name]
    
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
        self._state.make_static()


class OpenView(AtomicView):
    def __init__(self, db: Database, version_id: Database.VersionID):
        if not db._is_open(version_id):
            raise YBDBException('Cannot input a closed version id to an OpenVersionView')
        super().__init__(db, version_id)
        self.affecting_versions: Set[database.VersionID] = self._calculate_affecting_versions()
    
    def sync_from_db(self) -> None:
        self._state = self.db.compute_state(self.version_id)
        self.affecting_versions = self._calculate_affecting_versions()
    
    def _calculate_affecting_versions(self):
        revisions = self.db._revision_state(self.version_id).keys()
        return {self.version_id} | revisions


class OpenChangeView(OpenView):
    def __init__(self, db: Database, version_id: Database.VersionID):
        super().__init__(db, version_id)
        previous_version_id = self.db._get_version(self.version_id).previous
        current_revision_state = self.db._revision_state(self.version_id)
        self._previous_state = self.db.compute_state(previous_version_id, current_revision_state)

    def sync_from_db(self):
        super().sync_from_db()
        previous_version_id = self.db._get_version(self.version_id).previous
        current_revision_state = self.db._revision_state(self.version_id)
        self._previous_state = self.db.compute_state(previous_version_id, current_revision_state)


# class BranchEndView(EditableVersionView):
#     def __init__(self, database: Database, branch_id: BranchID):
#         super().__init__(database)
#         self.database = database
#         self.branch_id = branch_id

#         self.version_id = None
#         self.affecting_versions = None
#         self._view = None
#         self._previous_view = None

#         self.sync_from_db()
    
#     def sync_from_db(self):
#         self.version_id = self._to_version_id(self.branch_id)
#         previous_version_id = self._to_version_id(self.branch_id, allow_open=False)

#         self._view = self.compute_state(self.version_id)
#         self._view._callback = self.sync_to_db
#         self._previous_view = self.compute_state(previous_version_id)
#         revisions = self._revision_state(self.version_id).keys()
#         self._affecting_versions = {self.version_id} | revisions
    
#     def sync_to_db(self):
#         delta = json_interface.calculate_delta(self._previous_view, self._view)
#         self.update(self.branch_id, delta) # TODO unchecked
#         self.sync_from_view(self)
    
#     # def 
