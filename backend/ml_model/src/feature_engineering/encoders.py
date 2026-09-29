"""Inference-safe transformers shared with model training."""
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        self.mapping_ = {
            col: X[col].value_counts(normalize=True).to_dict() for col in X.columns
        }
        return self

    def transform(self, X):
        X = pd.DataFrame(X).copy()
        for col in X.columns:
            X[col] = X[col].map(getattr(self, 'mapping_', {}).get(col, {})).fillna(0)
        return X.values
