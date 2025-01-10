# model.py

import pickle
import os

class DITAModel:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.load_model()

    def load_model(self):
        vectorizer_path = os.path.join("models", "vectorizer.pkl")
        model_path = os.path.join("models", "model.pkl")

        if os.path.exists(vectorizer_path) and os.path.exists(model_path):
            with open(vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
        else:
            raise FileNotFoundError("Model or vectorizer not found. Please train the model first.")

    def predict_compliance(self, dita_content: str) -> float:
        """Returns probability of compliance (e.g., 0.0 to 1.0)."""
        if not self.model or not self.vectorizer:
            raise ValueError("Model or vectorizer is not loaded.")

        features = self.vectorizer.transform([dita_content])
        # .predict_proba() returns [ [prob_class_0, prob_class_1] ]
        prob = self.model.predict_proba(features)[0][1]
        return prob
