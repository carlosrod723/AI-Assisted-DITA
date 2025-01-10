import os
import shutil
import pickle
import unittest
import glob
from lxml import etree
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

# Import the functions you want to test
from backend.train_model import extract_text_from_xml, load_data, train

class TestDITAProcessing(unittest.TestCase):

    DATA_DIR = "data"  # Point to your data directory
    TEST_DATA_DIR = "test_data"  # Create this directory for minimal test files

    @classmethod
    def setUpClass(cls):
        # Create test data directory (optional)
        os.makedirs(cls.TEST_DATA_DIR, exist_ok=True)

    def test_extract_text_from_xml(self):
        xml_content = """<concept><title>Test</title><shortdesc>Desc</shortdesc><p>Para</p></concept>"""
        extracted_text = extract_text_from_xml(xml_content)
        self.assertEqual(extracted_text, "Test Desc Para")

        xml_content_with_invalid_syntax = """<concept><title>Test</title><shortdesc>Desc</shortdesc><p>Para<p></concept>"""
        extracted_text_invalid = extract_text_from_xml(xml_content_with_invalid_syntax)
        self.assertEqual(extracted_text_invalid, "") # Should return empty string for invalid XML

    def test_load_data(self):
        # Test with real data (assuming data directory exists)
        if not os.path.exists(self.DATA_DIR):
            raise  # Raise an error if data directory doesn't exist
        X, y = load_data(self.DATA_DIR)
        self.assertGreater(len(X), 0)  # Ensure some data is loaded
        self.assertEqual(len(X), len(y))

        # Test with minimal test data (optional)
        X_test, y_test = load_data(self.TEST_DATA_DIR)
        self.assertEqual(len(X_test), 0)  # No data in the empty test directory

    def test_training(self):
        train(self.DATA_DIR)

        # Check if model files were created
        self.assertTrue(os.path.exists("models/vectorizer.pkl"))
        self.assertTrue(os.path.exists("models/model.pkl"))

        # Load the model and vectorizer to test prediction (optional)
        with open("models/vectorizer.pkl", "rb") as f:
            vectorizer = pickle.load(f)
        with open("models/model.pkl", "rb") as f:
            model = pickle.load(f)

        test_text = "Another test paragraph."
        features = vectorizer.transform([test_text])
        prediction = model.predict(features)
        self.assertIn(prediction[0], [0,1]) # Very basic check, the data is too small to be accurate

    @classmethod
    def tearDownClass(cls):
        # Clean up test data (optional)
        shutil.rmtree(cls.TEST_DATA_DIR, ignore_errors=True)  # Ignore if it doesn't exist

if __name__ == "__main__":
    unittest.main()