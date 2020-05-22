"""rmq_pyctx_caller/__init__.py

The rmq_pyctx_caller package is callable from the command line via

    python -m rmq_pyctx_caller

This will import `CTX_MODULE.CTX_NAME`, and set it up using a `with` statement.
The context manager's `__enter__` method must return a callable. Then, for each
line of stdin, rmq_pyctx_caller will parse the line as JSON, preprocess it
using the jq program `ARG_ADAPTER`, and call the context manager's yielded
callable using the preprocessed JSON object as keyword arguments. Finally,
rmq_pyctx_caller will print (on one line) a JSON object with the "result" key
holding the result of the function call and the "orig" key holding the original
object.

created: MAY 2020
"""

__version__ = '0.1.0'
