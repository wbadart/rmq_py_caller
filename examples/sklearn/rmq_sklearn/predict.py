"""rmq_sklearn/predict.py

Run the fish AI on some input data.
created: MAY 2020
"""

from argparse import ArgumentParser
from contextlib import contextmanager
from functools import partial

import joblib
import pandas as pd

COLUMNS = ["Weight", "Length1", "Length2", "Length3", "Height", "Width"]


def predict(data, model):
    df = pd.DataFrame.from_records(data, columns=COLUMNS)
    df["Prediction"] = model.predict(df)
    return df.to_dict(orient="records")


@contextmanager
def setup_inference(path="tree.joblib"):
    model = joblib.load(path)
    yield partial(predict, model=model)
