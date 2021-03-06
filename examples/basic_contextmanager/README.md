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
- `with ... as fs` calls the context manager's `__enter__` method &mdash; it
  "enters" the context &mdash; which takes care of setup (in this case,
  acquiring a file handle from the OS), binding `__enter__`'s return value to
  `fs`.
- Then Python runs the body of the `with` statement
- If the body raises an uncaught exception, Python calls the context manager's
  `__exit__` method with information about the error, allowing the context
  manager to perform any cleanup (like releasing the file handle)
- If no exceptions are raised, Python calls `__exit__` after the last line of
  the body
  
Using a context manager ensures that resources get cleaned up, even when errors
are thrown.

Let's suppose `users.json` is our user database.
[`contextmanager.py`](./contextmanager.py) defines a context manager that can
be used to process incoming JSON data using this database:

```py
class UserDB:
    """Manage the user/ favorite number database."""

    def __init__(self, db_path="users.json"):
        self.db_path = db_path

    def query(self, name, number):
        """
        Record/ update a user's favorite number. Return True if a new user was
        created, else return False.
        """
        is_new_user = name not in self.db
        self.db[name] = number
        return is_new_user

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
```

The function we want to run on our RabbitMQ data, `UserDB.query`, requires some
setup: loading the database into memory. It also requires some teardown: saving
the updates to disk.

Let's check the initial state of the user database:

```sh
$ cat users.json
{"alice": 1234, "bob": 5678}
```

Because `UserDB`'s `__enter__` method returns the function we want to use, we
can simply provide rmq_py_caller an instance of `UserDB`:

```sh
PY_SETUP='from contextmanager import UserDB' \
    PY_TARGET='UserDB()' \
    ARG_ADAPTER='[.username, .info.favorite_number]' \
    python -m rmq_py_caller
```

If we needed to customize our `UserDB` instance, we can simply initialize it
with different values, e.g.:

```sh
PY_SETUP='from contextmanager import UserDB' \
    PY_TARGET='UserDB(db_path="other.json")' \
    ARG_ADAPTER='[.username, .info.favorite_number]' \
    python -m rmq_py_caller
```

This `ARG_ADAPTER` will pass the `username` property of input data as the first
argument to `query`, and `info.favorite_number` as the second.

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

The result is `false` since `"alice"` was already a user.

After pressing enter, press <kbd>Ctrl-d</kbd> to stop giving input to
rmq_py_caller. If we check out user database again, we can see that the
expected changes have been persisted:

```sh
$ cat users.json
{"alice": 82, "bob": 5678, "jo": 42}
```

We see our new user `"jo"` as well as `"alice"`'s updated favorite number.

You can really get creative with `__exit__`. For example, you could have
`query` collect metrics about when it's called and what it's called with, then
send those metrics to Elasticsearch on shutdown (in this case though, you'd
probably want a coroutine in `UserDB` to flush metrics updates periodically).
