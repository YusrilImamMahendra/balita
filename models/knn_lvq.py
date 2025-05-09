import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pickle
import pandas as pd

class KNN_LVQ:
    def __init__(self, k=3):
        self.k = k
        self.scaler = MinMaxScaler()
        self.prototypes = None

    def fit(self, X, y, epochs=100, learning_rate=0.01):
        X_scaled = self.scaler.fit_transform(X)
        classes = np.unique(y)
        self.prototypes = {c: np.mean(X_scaled[y == c], axis=0) for c in classes}
        
        for _ in range(epochs):
            for i in range(len(X_scaled)):
                x = X_scaled[i]
                true_class = y[i]
                distances = {c: np.linalg.norm(x - p) for c, p in self.prototypes.items()}
                winner_class = min(distances, key=distances.get)
                
                if winner_class == true_class:
                    self.prototypes[winner_class] += learning_rate * (x - self.prototypes[winner_class])
                else:
                    self.prototypes[winner_class] -= learning_rate * (x - self.prototypes[winner_class])
    
    def save_dataset(self, X, y, file_path):
        data = pd.DataFrame(X, columns=['feature1', 'feature2', ...])  # Replace ellipsis with actual feature names
        data['target'] = y
        data.to_csv(file_path, index=False)
    
    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        predictions = []
        for x in X_scaled:
            distances = {c: np.linalg.norm(x - p) for c, p in self.prototypes.items()}
            k_nearest = sorted(distances.items(), key=lambda x: x[1])[:self.k]
            prediction = max(set([item[0] for item in k_nearest]), key=[item[0] for item in k_nearest].count)
            predictions.append(prediction)
        return predictions
    
    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)