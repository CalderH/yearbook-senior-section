from abc import ABC, abstractmethod
from typing import List
import database
from database import Database
import json_interface

class View(ABC):
    def __init__(self, database: database.Database):
        self.database = database


class EditableVersionView(View):
    def __init__(self, database: Database):
        super().__init__(database)
        self.version_id = None
        self.affecting_versions = None
    
    @abstractmethod
    def sync_from_db(self):
        pass

    @abstractmethod
    def sync_to_db(self):
        pass


class BranchEndView(EditableVersionView):
    def __init__(self, database: Database, branch_id: database.BranchID):
        super().__init__(database)
        self.database = database
        self.branch_id = branch_id

        self.sync_from_db()
    
    def sync_from_db(self):
        self.version_id = self.database._to_version_id(self.branch_id)
        previous_version_id = self.database._to_version_id(self.branch_id, allow_open=False)

        self._view = self.database.compute_state(self.version_id)
        self._view._callback = self.broadcast_update
        self._previous_view = self.database.compute_state(previous_version_id)
        revisions = self.database._revision_state(self.version_id).keys()
        self._affecting_versions = {self.version_id} | revisions
    
    def sync_to_db(self):
        delta = json_interface.calculate_delta(self._previous_view, self._view)
        self.database.update(self.branch_id, delta) # TODO unchecked
        self.database.sync_from_view(self)
