from sklearn.linear_model import LogisticRegression

class CandleModel:
    def __init__(self):
        self.m = LogisticRegression()
        self.trained = False

    def fit(self, X, y):
        self.m.fit(X, y)
        self.trained = True

    def predict(self, X):
        return self.m.predict_proba(X)