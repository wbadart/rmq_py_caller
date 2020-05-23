For a lighter-weight solution to resource management than writing up a whole
context manager class, use [`@contextlib.contextmanager`][contextlib].

[contextlib]: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

For example:

```py
from contextlib import contextmanager
from functools import partial

def model_prediction(data, model):
    return model.predict(data)
    
@contextmanager
def setup_model():
    pretrained_model = my_framework.load_weights("/path/to/model.dat")
    try:
        yield partial(model_prediction, model=pretrained_model)
    finally:
        print("Doing some cleanup...")
```

The `try...finally` block ensures the cleanup gets run even if an exception was
raised.

This is a very lightweight approach to dependency injection for rmq_py_caller
functions. In fact, we don't even need a context manager if dependency
injection (rather than resource management) is our only goal:

```py
def setup_model():
    pretrained_model = my_framework.load_weights("path/to/model.dat")
    return partial(model_prediction, model=pretrained_model)
```

See [`examples/sklearn/`](../sklearn) for elaboration on this approach.
