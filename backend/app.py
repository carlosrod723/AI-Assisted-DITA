# app.py

import os
import pickle
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from lxml import etree

########################################
# 1. Create a single FastAPI app
########################################
app = FastAPI()

# Add CORS Middleware right after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["null"] if you only want to allow file://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

########################################
# 2. Load Pickled Vectorizer and Model
########################################
MODELS_DIR = "models"

vectorizer_path = os.path.join(MODELS_DIR, "vectorizer.pkl")
model_path = os.path.join(MODELS_DIR, "model.pkl")

with open(vectorizer_path, "rb") as f:
    vectorizer = pickle.load(f)

with open(model_path, "rb") as f:
    model = pickle.load(f)

########################################
# 3. Helper Function: Extract Text from XML
########################################
def extract_text_from_xml(xml_str: str) -> str:
    """
    Parse the XML string and extract all text content from DITA elements.
    Returns a single string of natural language tokens.
    """
    try:
        root = etree.fromstring(xml_str.encode("utf-8"))
        text_nodes = root.xpath("//text()")
        return " ".join(text_nodes)
    except Exception:
        # If XML is invalid or parsing fails, return an empty string
        return ""

########################################
# 4. Rule-Based Checks
########################################
def perform_rule_based_checks(root_element) -> list:
    """
    Perform multiple DITA checks on the parsed root element (an _Element).
    Return a list of error messages, if any.
    """
    errors = []

    # root_element is already the root (<concept>, <task>, or <reference>)
    root_tag = root_element.tag  # e.g. "concept", "task", "reference"

    # A. Check if the root tag is one of the expected
    if root_tag not in ["concept", "task", "reference"]:
        errors.append(f"Root element <{root_tag}> is unexpected. (Expected concept, task, or reference.)")

    # B. Check if the root has 'id' attribute
    if "id" not in root_element.attrib:
        errors.append(f"Root element <{root_tag}> is missing the 'id' attribute.")

    # C. Check for <concept> missing <title>
    for concept in root_element.findall(".//concept"):
        title_element = concept.find("title")
        if title_element is None:
            errors.append("Concept element is missing a <title>.")

    # D. Check for <task> missing <title>
    for task in root_element.findall(".//task"):
        title_element = task.find("title")
        if title_element is None:
            errors.append("Task element is missing a <title>.")
        # Optionally check if <taskbody> or <steps> exist

    # E. Check for <reference> missing <title>
    for ref in root_element.findall(".//reference"):
        title_element = ref.find("title")
        if title_element is None:
            errors.append("Reference element is missing a <title>.")

    return errors

########################################
# 5. Define Routes
########################################
@app.get("/")
def root():
    """
    Simple health check endpoint.
    """
    return {"message": "DITA AI Assistant - Backend is running"}

@app.post("/validate")
async def validate_dita(file: UploadFile = File(...)):
    """
    1. Reads the uploaded `.dita` file.
    2. Applies rule-based checks (missing <title>, invalid root, etc.).
    3. Extracts plain text and gets a compliance probability from the ML model.
    4. Returns JSON with `compliance_probability` and any structural `errors`.
    """
    content = await file.read()

    # Parse the XML
    try:
        root_element = etree.fromstring(content)
    except Exception as e:
        return {"error": f"Invalid XML: {str(e)}"}

    # Run rule-based checks
    errors = perform_rule_based_checks(root_element)

    # ML compliance score
    dita_text = extract_text_from_xml(content.decode("utf-8"))
    X_features = vectorizer.transform([dita_text])
    compliance_probability = float(model.predict_proba(X_features)[0][1])

    return {
        "compliance_probability": compliance_probability,
        "errors": errors
    }

########################################
# 6. Main Entrypoint
########################################
if __name__ == "__main__":
    # Start the server: uvicorn app:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
