import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import MinMaxScaler
from copy import deepcopy

class KNN(BaseEstimator, ClassifierMixin):
    """
    K-Nearest Neighbors classifier dengan bobot.
    Mengimplementasikan scikit-learn estimator interface.
    """
    def __init__(self, k=3, bobot=None):
        # Store parameters exactly as passed
        self.k = k
        self.bobot = bobot
        
    def _get_bobot(self):
        """Helper method untuk mendapatkan bobot dalam format numpy array"""
        if self.bobot is None:
            return np.ones(3)
        return np.array(self.bobot)
        
    def fit(self, X, y):
        """Fit model dengan data training"""
        # Initialize attributes that aren't parameters
        self.scaler_ = MinMaxScaler()
        self.X_train_ = self.scaler_.fit_transform(X)
        self.y_train_ = np.array(y)
        # Initialize bobot array
        self.bobot_ = self._get_bobot()
        return self
        
    def predict(self, X):
        """Prediksi kelas untuk sampel X"""
        check_is_fitted = getattr(BaseEstimator, "_check_is_fitted", None)
        if check_is_fitted is not None:
            check_is_fitted(self)
        else:
            if not hasattr(self, 'X_train_'):
                raise ValueError("Model belum di-fit dengan data training")
            
        X_scaled = self.scaler_.transform(X)
        predictions = []
        
        for x in X_scaled:
            # Pastikan bobot sesuai dengan jumlah fitur
            weights = self.bobot_[:X.shape[1]]
            if len(weights) < X.shape[1]:
                weights = np.pad(weights, (0, X.shape[1] - len(weights)), 
                               'constant', constant_values=1)
                
            # Hitung jarak dengan bobot
            distances = np.sqrt(np.sum(weights * (self.X_train_ - x) ** 2, axis=1))
            
            # Ambil k tetangga terdekat
            idx_knn = np.argsort(distances)[:self.k]
            labels_knn = self.y_train_[idx_knn]
            
            # Voting mayoritas
            unique, counts = np.unique(labels_knn, return_counts=True)
            predictions.append(unique[np.argmax(counts)])
            
        return np.array(predictions)
        
    def score(self, X, y):
        """Implementasi score untuk scikit-learn compatibility"""
        return np.mean(self.predict(X) == y)
        
    def get_params(self, deep=True):
        """Get parameters for this estimator."""
        return {'k': self.k, 'bobot': self.bobot}
        
    def set_params(self, **parameters):
        """Set the parameters of this estimator."""
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self