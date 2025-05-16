import numpy as np
from sklearn.preprocessing import MinMaxScaler

class KNN:
    def __init__(self, k=3, bobot=(1,1,1)):
        self.k = k
        self.bobot = np.array(bobot)
        self.scaler = MinMaxScaler()

    def fit(self, X, y):
        self.X_train = self.scaler.fit_transform(X)
        self.y_train = np.array(y)

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        predictions = []
        for x in X_scaled:
            distances = np.sqrt(np.sum(self.bobot * (self.X_train - x) ** 2, axis=1))
            idx_knn = np.argsort(distances)[:self.k]
            labels_knn = self.y_train[idx_knn]
            unique, counts = np.unique(labels_knn, return_counts=True)
            predictions.append(unique[np.argmax(counts)])
        return predictions