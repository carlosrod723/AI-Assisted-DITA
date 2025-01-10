# train_model.py

import os
import glob
import pickle
import re
from lxml import etree
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

def extract_text_from_xml(xml_str: str) -> str:
    """
    Parse the XML string and extract all text content from DITA elements.
    This ensures we feed natural language tokens (instead of raw XML) to CountVectorizer.
    """
    try:
        # Convert string to bytes, parse with lxml
        root = etree.fromstring(xml_str.encode("utf-8"))
        # Collect text from all nodes (e.g., <title>, <shortdesc>, <p>, etc.)
        text_nodes = root.xpath("//text()")
        # Join them with spaces to form one coherent text
        return " ".join(text_nodes)
    except Exception:
        # If parsing fails (invalid XML syntax, etc.), return an empty string to avoid crashing
        return ""

def load_data(data_path: str = "data"):
    """
    Reads all .dita files from `data_path` subfolders 'compliant' and 'non_compliant',
    extracts plain text, and returns lists of documents (X) and labels (y).

    Label 1 = Compliant, 0 = Non-Compliant
    """
    compliant_files = glob.glob(os.path.join(data_path, "compliant", "*.dita"))
    non_compliant_files = glob.glob(os.path.join(data_path, "non_compliant", "*.dita"))

    X = []
    y = []

    # Handle compliant files
    for file in compliant_files:
        with open(file, "r", encoding="utf-8") as f:
            raw_xml = f.read()
            text_content = extract_text_from_xml(raw_xml)
            X.append(text_content)
        y.append(1)

    # Handle non-compliant files
    for file in non_compliant_files:
        with open(file, "r", encoding="utf-8") as f:
            raw_xml = f.read()
            text_content = extract_text_from_xml(raw_xml)
            X.append(text_content)
        y.append(0)

    return X, y

def train(data_path: str = "data"):
    """
    Trains a simple logistic regression classifier using the .dita files in `data_path`.
    By default, looks in:

        data/
        ├── compliant/
        └── non_compliant/

    for labeled data.
    """
    print(f"Loading data from: {data_path}")
    X, y = load_data(data_path)

    # Quick debug: show the first doc if available
    if X:
        print("Example of extracted text from the first doc:\n", X[0][:200], "...\n")

    # Convert text to numeric features
    vectorizer = CountVectorizer(stop_words=None)
    X_features = vectorizer.fit_transform(X)

    if X_features.shape[1] == 0:
        raise ValueError(
            "Empty vocabulary! Your .dita files might not contain enough text, "
            "or all text is being stripped out. Check your extraction logic."
        )

    # Train a logistic regression model
    model = LogisticRegression()
    model.fit(X_features, y)
    print("Model training complete.")

    # Ensure we have a 'models' folder
    if not os.path.exists("models"):
        os.mkdir("models")

    # Save the vectorizer
    vectorizer_path = os.path.join("models", "vectorizer.pkl")
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)

    # Save the trained model
    model_path = os.path.join("models", "model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print(f"Model and vectorizer saved to {os.path.abspath('models/')}")

if __name__ == "__main__":
    train()
