from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from lightgbm import LGBMClassifier


def fit_logistic(X, y, params):
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    clf = LogisticRegression(**params)
    clf.fit(Xs, y)
    return _WrappedPipeline(clf, scaler)


def fit_lightgbm_monotone(X, y, params, eval_X=None, eval_y=None):
    clf = LGBMClassifier(**params)
    clf.fit(X, y, eval_X=eval_X, eval_y=eval_y)
    return clf


class _WrappedPipeline:
    def __init__(self, model, scaler):
        self.model = model
        self.scaler = scaler

    def predict_proba(self, X):
        return self.model.predict_proba(self.scaler.transform(X))
