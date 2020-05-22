# rmq_py_caller

Call a Python function on JSON from [RabbitMQ][rmq]. Supports [context
managers][ctx] for when the function needs setup or teardown.

[ctx]: https://docs.python.org/3/library/contextlib.html
[rmq]: https://www.rabbitmq.com

## Usage

The simplest way to use rmq_py_caller is the CLI. To start, install the
package:

```sh
pip install git+https://github.com/Badart-William/rmq_py_caller.git
```

You can now call the package directly from the command line with `python -m
rmq_py_caller`, just make sure to set the following environment variables:

Environment Variable | Description
---------------------|------------
`PY_TARGET`   | The name of the function* to call
`PY_SETUP`    | (_Optional_) Initialization code (such as importing the function)
`ARG_ADAPTER` | A [`jq`][jq] program mapping input data to arguments

[jq]: https://stedolan.github.io/jq

\* `PY_TARGET` can also identify a context manager, provided its `__enter__`
method returns the function of interest. This is useful if the function
requires some setup before running, such as loading a data file, or teardown afterwards.

For example:

```sh
PY_TARGET='len' ARG_ADAPTER='[.]' python -m rmq_py_caller < data.ndjson
```

will compute the length of each array listed in the [newline-delimited
JSON][ndjson] file `data.ndjson`. `ARG_ADAPTER` should be an array which
arranges the arguments to `PY_TARGET`. To illustrate, here's a slightly more
involved example where `PY_TARGET` takes two arguments:

```sh
PY_SETUP='from operator import add' \
    PY_TARGET=add \
    ARG_ADAPTER='[.a, .b]' \
    python -m rmq_py_caller < data.ndjson
```

This setup will, for each _object_ in `data.ndjson`, compute the sum of the
object's `a` and `b` attributes.

[ndjson]: http://ndjson.org

### Docker

Processing JSON data from stdin is useful for debugging, but you're probably
here because you want to process JSON data from RabbitMQ. If this is the case,
the provided Docker image is the way to go.

The container uses the environment variables listed above, and also expects:

Environment Variable | Description
---------------------|------------
`INPUT_QUEUE`        | Queue from which to grab input data
`OUTPUT_EXCHANGE`    | Exchange to which results are published
`OUTPUT_ROUTING_KEY` | (_Optional_) Routing key with which to publish results
`RABTAP_AMQPURI`     | Location of broker (see the [`rabtap`][rabtap uri] URI spec)
`OUTPUT_ADAPTER`     | (_Default: `.result`_) `jq` post-processing program

[rabtap uri]: https://github.com/jandelgado/rabtap#broker-uri-specification

To continue the `len` example from above:

```sh
docker run --rm -it \
    -e PY_TARGET=len \
    -e ARG_ADAPTER='[.]' \
    -e INPUT_QUEUE=data_in \
    -e OUTPUT_EXCHANGE=data_out \
    -e RABTAP_AMQPURI=amqp://guest:guest@host.docker.internal:5672/ \
    wbadart/rmq_py_caller
```

will, for each array posted to the `data_in` queue, compute its length and
publish the result to the `data_out` exchange. Note that inside a container,
`host.docker.internal` resolves to the IP address of the Docker host; you can
use it to access services you'd get via `localhost` outside the container.
