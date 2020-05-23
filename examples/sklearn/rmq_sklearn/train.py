"""rmq_sklearn/train.py

This highly advanced model represents the pinnacle of machine learning.
created: MAY 2020
"""

from argparse import ArgumentParser

import joblib
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


def train(df, model_path):
    labels = df.pop("Species")
    X_train, X_test, y_train, y_test = train_test_split(df, labels)

    model = DecisionTreeClassifier(max_depth=8)
    model.fit(X_train, y_train)

    print(classification_report(y_test, model.predict(X_test)))
    joblib.dump(model, model_path)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "-f", "--file", default="data/fish.csv", help="path to training data")
    parser.add_argument(
        "-m", "--model", default="tree.joblib", help="path to save model")
    args = parser.parse_args()
    df = pd.read_csv(args.file)
    train(df, args.model)


if __name__ == "__main__":
    main()
