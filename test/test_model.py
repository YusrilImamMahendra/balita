import unittest
import numpy as np
from models.knn import KNN_LVQ

class TestKNNLVQ(unittest.TestCase):
    def setUp(self):
        self.model = KNN_LVQ(k=3)
        self.X_train = np.array([[1,2], [1,4], [2,3], [4,5], [4,7]])
        self.y_train = np.array(['A','A','B','B','B'])
    
    def test_fit_and_predict(self):
        self.model.fit(self.X_train, self.y_train)
        predictions = self.model.predict(np.array([[1,3]]))
        self.assertIn(predictions[0], ['A','B'])

if __name__ == '__main__':
    unittest.main()