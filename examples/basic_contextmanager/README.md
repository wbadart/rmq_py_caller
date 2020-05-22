rmq_py_caller advertises support for _context managers_. What does this mean? A
context manager is a Python construct for cleanly expressing setup, teardown,
and exception handling. Context managers are the object of `with` syntax, e.g.:

```py
with open("users.json") as fs:
    print(fs.read())
```

Let's break it down:

- `open("users.json")` constructs a context manager for handling the
  `"users.json"` file resource
- `with ... as fs` calls the context manager's `__enter__` method, which takes
  care of setup (in this case, acquiring a file handle from the OS), binding
  the return value to `fs`.
- Then Python runs the body of the `with` statement
- If any code in the body raises an exception, Python calls the context
  manager's `__exit__` method with information about the error, allowing the
  context manager to perform an cleanup (like releasing the file handle)
- If no exceptions are raised, Python calls `__exit__` after the last line of
  the body
  
Using a context manager ensures that resources get cleaned up, even when errors
are thrown.

Let's suppose `users.json` is our user database. `contextmanager.py` defines a
context manager that can be used to process incoming JSON data using this
database:

```py
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
        with open("users.json") as fs:
            self.db = json.load(fs)
        # return the method we want rmq_py_caller to use
        return self.query

    def __exit__(self, *_):
        # Flush the DB updates
        with open("users.json", "w") as fs:
            json.dump(self.db, fs)
```

The function we want to run on our RabbitMQ data, `UserDB.query`, requires some
setup: loading the database into memory. It also requires some teardown: saving
the updates to disk.

Let's check the initial state of the user database:

```sh
$ cat users.json
{"alice": 1234, "bob": 5678}
```

Because the context manager's `__enter__` method returns the function we want
to use, we can give it straight to rmq_py_caller:

```sh
PY_SETUP='from contextmanager import UserDB' \
    PY_TARGET='UserDB' \
    ARG_ADAPTER='[.username, .info.favorite_number]' \
    python -m rmq_py_caller
```

rmq_py_caller is now waiting for input. Let's try pasting in this object to
simulate a message from RabbitMQ:

```json
{"username": "jo", "info": {"favorite_number": 42}}
```

Be sure to press enter! You should see that the `"result"` is `true` since a
new user was created (the behavior laid out by `query`'s docstring). Now let's
try:

```json
{"username": "alice", "info": {"favorite_number": 82}}
```

After pressing enter, press <kbd>Ctrl-d</kbd> to stop giving input to
rmq_py_caller. If we check out user database again, we can see that the
expected changes have been persisted:

```sh
$ cat users.json
{"alice": 1316, "bob": 5678, "jo": 42}
```

You can really get creative with `__exit__`. For example, you could have
`query` collect metrics about when it's called and what it's called with, then
send those metrics to Elasticsearch on shutdown (in this case though, you'd
probably want a coroutine in `UserDB` to flush metrics updates periodically).

Note, if we wanted to use a different user database, we can use `INIT_ARGS` to
specify how rmq_py_caller should initialize `UserDB`:

```sh
PY_SETUP='from contextmanager import UserDB' \
    PY_TARGET='UserDB' \
    ARG_ADAPTER='[.username, .info.favorite_number]' \
    INIT_ARGS='{"db_path": "other.json"}' \
    python -m rmq_py_caller
```
