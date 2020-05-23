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
functions. In fact, it can be even shorter if no cleanup is required:

```py
@contextmanager
def setup_model():
    pretrained_model = my_framework.load_weights("path/to/model.dat")
    yield partial(model_prediction, model=pretrained_model)
```

Note: we'd need to set `CTX_INIT_ARGS` to use `setup_model`. Otherwise,
rmq_py_caller won't initialize the context (calling `load_weights` and such)
before trying to enter it.

See [`examples/sklearn/`](../sklearn) for further elaboration on this approach.
