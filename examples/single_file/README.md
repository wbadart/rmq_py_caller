Here we have a standalone module, `single_file.py`, that defines a function
we'd like to hook up to RabbitMQ, `length_of_longest_element`. First, let's
spin it up with rmq_py_caller (sans RabbitMQ) with a little sample data:

```
$ PY_SETUP='from single_file import length_of_longest_element' \
    PY_TARGET=length_of_longest_element \
    ARG_ADAPTER='[.]' \
    python -m rmq_py_caller < sample.ndjson
{"result": 6, "orig": ["foo", "barbaz"]}
{"result": 5, "orig": [[1, 2, 3, 4, 5], [6, 7, 8], [9]]}
```

The longest entry of `["foo", "barbaz"]`, the first line, is `"barbaz"`, which
is 6 characters long (hence `"result": 6`). You can read the results for the
second line similarly.

Now, in order to talk to RabbitMQ, we need a way to get our lonely module into
a container. There are several ways to do this, such as creating a custom image
`FROM wbadart/rmq_py_caller`, but the quickest is simply to mount it in:

```sh
docker run --rm -it -v $PWD:/src -w /src \
    -e PY_SETUP='from single_file import length_of_longest_element' \
    -e PY_TARGET=length_of_longest_element \
    -e ARG_ADAPTER='[.]' \
    -e INPUT_QUEUE=data_in \
    -e OUTPUT_EXCHANGE=data_out \
    -e RABTAP_AMQPURI=amqp://guest:guest@host.docker.internal:5672/ \
    wbadart/rmq_py_caller
```
