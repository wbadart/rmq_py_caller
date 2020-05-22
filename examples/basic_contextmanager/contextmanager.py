"""contextmanager.py

Setup a connection to the user database, process incoming records, then tear
down the connection.

created: MAY 2020
"""

import json


class UserDB:
    """Manage the user/ favorite number database."""

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
        with open("users.json") as fs:
            self.db = json.load(fs)
        # return the method we want rmq_py_caller to use
        return self.query

    def __exit__(self, *_):
        # Flush the DB updates
        with open("users.json", "w") as fs:
            json.dump(self.db, fs)


# rmq_py_caller won't instantiate UserDB for us; we'll use this instance as our
# PY_TARGET
ACTIVE_MANAGER = UserDB()
