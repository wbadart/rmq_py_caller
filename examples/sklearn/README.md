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
    ARG_ADAPTER='[.]' \
    python -m rmq_py_caller < data/sample.ndjson
```

You should see some gnarly output with each fish entry under `"result"` is
enriched by a `"Prediction"` field. Now let's use Docker to stand up our fish
prediction service. Skim `rmq_sklearn/predict.py`, `Dockerfile` and
`docker-compose.yml`, `pip install docker-compose` if you don't have it, and
run:

```sh
docker-compose up
```

Note: I'm counting on you already having a RabbitMQ server running on your
`localhost` with a `data_in` queue, a `data_out` fanout exchange, and another
queue bound to `data_out` with routing key `*`.

Once you see:

```text
...
Recreating sklearn_fish_prediction_1 ... done
Attaching to sklearn_fish_prediction_1
```

try copying and pasting the contents of `sample.ndjson` to the **Publish
message** section of `data_in`. Now click over to the queue you bound to
`data_out`, **Get messages**, and see that your fish predictions have been
published.
