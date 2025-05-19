import numpy as np
from sklearn.preprocessing import MinMaxScaler

class LVQ:
    def __init__(self, n_prototypes_per_class=1, learning_rate=0.1, n_epochs=100):
        self.n_prototypes_per_class = n_prototypes_per_class
        self.learning_rate = learning_rate
        self.n_epochs = n_epochs
        self.scaler = MinMaxScaler()

    def fit(self, X, y):
        X = self.scaler.fit_transform(X)
        classes = np.unique(y)
        # Inisialisasi prototipe: pilih acak dari data tiap kelas
        self.prototypes = []
        self.prototype_labels = []
        for cls in classes:
            idx = np.where(y == cls)[0]
            chosen_idx = np.random.choice(idx, self.n_prototypes_per_class, replace=False)
            self.prototypes.extend(X[chosen_idx])
            self.prototype_labels.extend([cls] * self.n_prototypes_per_class)
        self.prototypes = np.array(self.prototypes)
        self.prototype_labels = np.array(self.prototype_labels)
        # Training LVQ
        for epoch in range(self.n_epochs):
            for xi, yi in zip(X, y):
                # Cari prototipe terdekat
                dists = np.linalg.norm(self.prototypes - xi, axis=1)
                j = np.argmin(dists)
                # Update
                if self.prototype_labels[j] == yi:
                    self.prototypes[j] += self.learning_rate * (xi - self.prototypes[j])
                else:
                    self.prototypes[j] -= self.learning_rate * (xi - self.prototypes[j])

    def get_prototypes(self):
        # Prototipe dalam skala asli
        return self.scaler.inverse_transform(self.prototypes), self.prototype_labels