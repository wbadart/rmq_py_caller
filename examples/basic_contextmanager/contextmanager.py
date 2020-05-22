"""contextmanager.py

Setup a connection to the user database, process incoming records, then tear
down the connection.

created: MAY 2020
"""

import json


class UserDB:
    """Manage the user/ favorite number database."""

    def __init__(self, db_path="users.json"):
        self.db_path = db_path

    def query(self, name, number):
        """
        If the user is in the database, add `number` to their favorite number,
        otherwise, add the corresponding entry.

        Return True if a new user was created, else False.
        """
        if name in self.db:
            self.db[name] += number
            return False
        else:
            self.db[name] = number
            return True

    def __enter__(self):
        # Setup the database needed by `query`
        with open(self.db_path) as fs:
            self.db = json.load(fs)
        # return the method we want rmq_py_caller to use
        return self.query

    def __exit__(self, *_):
        # Flush the DB updates
        with open(self.db_path, "w") as fs:
            json.dump(self.db, fs)
