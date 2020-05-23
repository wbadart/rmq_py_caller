"""rmq_sklearn/predict.py

Run the fish AI on some input data.
created: MAY 2020
"""

from functools import partial

import joblib
import pandas as pd

COLUMNS = ["Weight", "Length1", "Length2", "Length3", "Height", "Width"]


def predict(data, model):
    df = pd.DataFrame.from_records(data, columns=COLUMNS)
    return model.predict(df).tolist()


def setup_inference(path="tree.joblib"):
    model = joblib.load(path)
    return partial(predict, model=model)
