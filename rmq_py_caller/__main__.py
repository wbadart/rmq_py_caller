"""rmq_pyctx_caller/__main__.py

Command line entry point. See `python -m rmq_py_caller --help` for details.
created: MAY 2020
"""

import logging
import sys
from argparse import ArgumentParser
from os import environ

import jq

from rmq_py_caller.app import main_loop


def main():
    """Execute PY_SETUP (if set) and call PY_TARGET on JSON from stdin. See
    https://github.com/wbadart/rmq_py_caller#readme for details.
    """
    parser = ArgumentParser(prog="python -m rmq_py_caller", description=main.__doc__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="-v to include info, -vv to include debugging",
    )
    args = parser.parse_args()

    # If you're curious about the use exec/ eval here, please see the project
    # wiki for discussion.
    # pylint: disable=exec-used,eval-used
    exec(environ.get("PY_SETUP", ""), globals())
    ctx = eval(environ["PY_TARGET"])

    # Wait until now to call basicConfig in case PY_SETUP wants to do it
    if args.verbose:
        logging.basicConfig(
            level=[logging.WARN, logging.INFO, logging.DEBUG][args.verbose]
        )
    log = logging.getLogger(__name__)
    log.debug("Got PY_TARGET: %s", ctx)
    adapter = jq.compile(environ.get("ARG_ADAPTER", "[.]"))
    log.debug("Using ARG_ADAPTER: %s", adapter.program_string)
    main_loop(ctx, adapter, sys.stdin)


if __name__ == "__main__":
    main()
