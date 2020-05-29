This directory is a little Python package that uses [Scikit-Learn][sklearn] to
run a decision tree on data. Here's how you might plug it in to your data
stream using rmq_py_caller.

[sklearn]: https://scikit-learn.org/stable/index.html

_(The dataset comes from [Kaggle][data].)_

[data]: https://www.kaggle.com/aungpyaeap/fish-market

Assuming you're in [this](.) directory, first train a model with the training
script, `rmq_sklearn/train.py`:

```sh
python -m rmq_sklearn.train
```

You now have a pre-trained model, saved to `tree.joblib`, which can be picked
up for your inference job. Let's test out inference with the regular
command-line invocation of rmq_py_caller:

```sh
PY_SETUP='from rmq_sklearn.predict import setup_inference' \
    PY_TARGET='setup_inference()' \
    python -m rmq_py_caller < data/sample.ndjson
```

You should see all the predictions under the `"result"` field of the output.
This will be rejoined with the input data by the `OUTPUT_ADAPTER`. In this
case, since the `predict` function has access to the entire input object, we
could have just as easily done the enrichment there.

Now let's use Docker to stand up our fish prediction service. Skim
[`rmq_sklearn/predict.py`](./rmq_sklearn/predict.py),
[`Dockerfile`](./Dockerfile) and[ `docker-compose.yml`](./docker-compose.yml),
`pip install docker-compose` if you don't have it, and run:

```sh
docker-compose up
```

Note: I'm counting on you already having a RabbitMQ server running on your
`localhost` with `data_in` and `data_in2` queues. You should also bind a queue
to `amq.fanout` to inspect results.

Once you see:

```text
...
Recreating sklearn_fish_prediction_1 ... done
Attaching to sklearn_fish_prediction_1
```

try copying and pasting the contents of `sample.ndjson` to the **Publish
message** section of `data_in`. Now click over to the queue you bound to
`amq.fanout`, **Get messages**, and see that your fish predictions have been
published.

Final side note: as our fish prediction service gains users, we can scale
horizontally pretty trivially:

```yaml
version: "3.4"
services:
  fish_prediction:
    build: .
    image: fish_prediction
    deploy:
      replicas: 10
    environment:
      # ...
    volumes:
      # ...
```

Each replica will be watching the same input queue, so messages to that queue
will be naturally distributed among the 10 consumers.

## Alternate Schema

What if we're getting requests for fish predictions from multiple sources? More
troubling, what if they have different ideas about how to represent a fish? No
problem! We just need map the new input schema to the arguments `predict` is
looking for. Let's say instead of

```json
{"Weight": 123, "Length1": 456, ...}
```

we have

```json
{"fish_weight": 321, "fish_length1": 654, ...}
```

There might even be extra fields. No worries. Looking at `predict.COLUMNS`, we
see that the `predict` function wants the weight feature in the first column,
length1 in the second, and so on.

```yaml
# ...
ARG_ADAPTER: >-
  [[.[] | [ 
    .fish_weight,
    .fish_length1,
    .fish_length2,
    .fish_length3,
    .fish_height,
    .fish_width,
  ]]]
# ...
```

You can test this arrangement by publishing the contents of
[`data/sample.schema2.ndjson`](./data/sample.schema2.ndjson) to `data_in2`.
