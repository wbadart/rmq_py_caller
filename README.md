# rmq_pyctx_caller

Call a Python [context manager][ctx] on JSON from [RabbitMQ][rmq]. Useful when
you have a function you want to call on lots of data, but it requires some
setup and/ or teardown.

[ctx]: https://docs.python.org/3/library/contextlib.html
[rmq]: https://www.rabbitmq.com

## Usage

rmq_pyctx_caller just needs two ingredients: a function and a context manager.
Specifically, a context manager whose `__enter__` method returns the function
of interest. It's easiest to use a Docker container. Simply add a Dockerfile
with the following contents to the project where you define your project:

```dockerfile
FROM wbadart/rmq_pyctx_caller
WORKDIR /src
COPY . .
RUN pip install .
```

Build the image (e.g. `docker build -t my_proj .`) and run the container,
setting the following environment variables:

Environment Variable | Description
---------------------|------------
`INPUT_QUEUE`          | Queue from which to grab input data
`OUTPUT_EXCHANGE`      | Exchange to which results are published
`OUTPUT_ROUTING_KEY`   | (_Optional_) Routing key with which to publish results
`RABTAP_AMQPURI`       | Location of broker (see the [`rabtap`][rabtap uri] URI spec)
`ARG_ADAPTER`          | [`jq`][jq] program to extract arguments from input
`OUTPUT_ADAPTER`       | (_Default: `.result`_) `jq` post-processing program
`CTX_NAME`             | Name of the target function's context manager
`CTX_MODULE`           | Module from which to import `CTX_NAME`

[rabtap uri]: https://github.com/jandelgado/rabtap#broker-uri-specification
[jq]: https://stedolan.github.io/jq

For example, let's say you have `my_proj/analyzer.py`:

```py
class my_proj_analyzer:
    def run(self, func_arg1, func_arg2):
        c = self.conn.cursor()
        c.execute(
            'SELECT * FROM user WHERE name=? AND joined>?',
            (func_arg1, func_arg2),
        )
        return len(c.fetchall())
        
    def __enter__(self):
        self.conn = sqlite3.connect("cool.db")
        return self.run
    
    def __exit__(self, *_):
        self.conn.close()
        emit_closing_metrics(self)
```

and `my_proj/__init__.py`:

```py
from my_proj.analyzer import my_proj_analyzer
```

Then running:

```sh
docker run --rm -it \
    -e INPUT_QUEUE=data_in \
    -e OUTPUT_EXCHANGE=data_out \
    -e RABTAP_AMQPURI=amqp://guest:guest@host.docker.internal:5672/ \
    -e ARG_ADAPTER='{func_arg1: .name, func_arg2: .meta.timestamp}' \
    -e CTX_NAME=my_proj_analyzer \
    -e CTX_MODULE=my_proj \
    my_proj
```

would run `my_proj_analyzer` roughly as follows:

```py
from my_proj import my_proj_analyzer

with my_proj_analyzer as func:
    for msg in INPUT_QUEUE:
        yield func(
            func_arg1=msg["name"],
            func_arg2=msg["meta"]["timestamp"],
        )
```

In other words, for every "query" routed to the `data_in` queue,
`my_proj_analyzer` will count the users with the matching `name` who joined
after the given `timestamp` and post the result to `data_out`.

Note, you can record the above in a `docker-compose.yml` file:

```yaml
version: "3.4"
services:
  my_proj:
    build: .
    image: my_proj
    environment:
    - INPUT_QUEUE: data_in
    - OUTPUT_EXCHANGE: data_out
    - RABTAP_AMQPURI: amqp://guest:guest@host.docker.internal:5672/
    - ARG_ADAPTER: "{func_arg1: .name, func_arg2: .meta.timestamp}"
    - CTX_NAME: my_proj_analyzer
    - CTX_MODULE: my_proj
```
