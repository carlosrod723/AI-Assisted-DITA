import os
import random
import string
import re
from faker import Faker

fake = Faker()

# Directories for compliant and non-compliant files
GOOD_FOLDER = "sample_data/compliant"
BAD_FOLDER = "sample_data/non_compliant"

# Define possible topic types
TOPIC_TYPES = ["concept", "task", "reference"]

# DOCTYPE lookup for each topic type
DOCTYPE_MAP = {
    "concept": '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">',
    "task": '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">',
    "reference": '<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">'
}

# --------------------------------------------------------------------
# 1. Generate Varied Content for Compliant Files
# --------------------------------------------------------------------
def generate_compliant_content(index):
    """
    Returns a well-formed DITA topic string (compliant).
    Randomly chooses concept/task/reference and populates with valid structure.
    """
    topic_type = random.choice(TOPIC_TYPES)
    doctype = DOCTYPE_MAP[topic_type]

    topic_id = f"{topic_type}_good_{index}"
    title = fake.sentence(nb_words=5)      # e.g., "Setting up the server"
    shortdesc = fake.sentence(nb_words=8)  # e.g., "This describes how to set up..."
    
    # Two random paragraphs for the body
    body_paragraphs = [
        f"<p>{fake.paragraph(nb_sentences=2)}</p>",
        f"<p>{fake.paragraph(nb_sentences=2)}</p>"
    ]

    if topic_type == "task":
        # For <task>, we often have <taskbody> with <steps>
        task_body = f"""
        <taskbody>
            <steps>
                <step>
                    <cmd>{fake.sentence(nb_words=3)}</cmd>
                    <info>{fake.sentence(nb_words=5)}</info>
                </step>
                <step>
                    <cmd>{fake.sentence(nb_words=3)}</cmd>
                    <info>{fake.sentence(nb_words=5)}</info>
                </step>
            </steps>
        </taskbody>
        """
        body_content = task_body
    elif topic_type == "reference":
        # For <reference>, we often have <refbody>
        ref_body = "\n        ".join(body_paragraphs)
        body_content = f"""
        <refbody>
            {ref_body}
        </refbody>
        """
    else:
        # Default to <concept> with <conbody>
        con_body = "\n        ".join(body_paragraphs)
        body_content = f"""
        <conbody>
            {con_body}
        </conbody>
        """

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
{doctype}
<{topic_type} id="{topic_id}">
    <title>{title}</title>
    <shortdesc>{shortdesc}</shortdesc>
    {body_content}
</{topic_type}>
"""
    return content


# --------------------------------------------------------------------
# 2. Generate Non-Compliant Content with Multiple Potential Errors
# --------------------------------------------------------------------
def introduce_error_missing_title(content):
    """
    Completely remove the <title>...</title> section.
    """
    return re.sub(r"<title>.*?</title>", "<!-- ERROR: Title removed -->", content, flags=re.DOTALL)

def introduce_error_misspelled_root_tag(content):
    """
    Finds the root DITA tag (<concept|<task|<reference>) and misspells it,
    e.g. <concept> -> <concpet>.
    """
    match = re.search(r"<(concept|task|reference)\b", content)
    if not match:
        return content  # If no match, just return unchanged
    actual_topic_type = match.group(1)  # e.g. "concept"

    # Simple way to misspell: swap last two letters (or add an 'x' if too short)
    if len(actual_topic_type) > 2:
        misspelled = (actual_topic_type[:-2] 
                      + actual_topic_type[-1] 
                      + actual_topic_type[-2])
    else:
        misspelled = actual_topic_type + "x"

    content = content.replace(f"<{actual_topic_type}", f"<{misspelled}")
    content = content.replace(f"</{actual_topic_type}>", f"</{misspelled}>")
    return content

def introduce_error_invalid_xml_syntax(content):
    """
    Inserts an unclosed <p tag somewhere to create invalid XML.
    """
    lines = content.split("\n")
    if len(lines) > 5:
        idx = random.randint(1, len(lines) - 2)
        lines[idx] = lines[idx] + " <p"  # Missing closing '>'
    return "\n".join(lines)

def introduce_error_missing_required_attribute(content):
    """
    Removes id="..." from the root element, if present.
    """
    return re.sub(r'id="[^"]*"', '', content)

def introduce_error_invalid_attribute_value(content):
    """
    Adds or replaces an attribute with something invalid (random string).
    Example: outputclass="abc123".
    """
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    new_attr = f' outputclass="{random_str}"'
    pattern = r"(<(concept|task|reference)\b[^>]*)(>)"
    return re.sub(pattern, r"\1" + new_attr + r"\3", content, count=1)

def introduce_error_incorrect_element_order(content):
    """
    Swap the order of <shortdesc> and <conbody> (or <taskbody>/<refbody>) if both exist.
    This may break well-formedness for certain DITA structures.
    """
    # Attempt a simple swap for concept
    if "<shortdesc>" in content and "<conbody>" in content:
        # Extract shortdesc block
        shortdesc_pattern = re.compile(r"<shortdesc>.*?</shortdesc>", re.DOTALL)
        shortdesc_match = shortdesc_pattern.search(content)
        if shortdesc_match:
            shortdesc_block = shortdesc_match.group(0)
            content = shortdesc_pattern.sub("<!--SHORTDESC_PLACEHOLDER-->", content, 1)

        # Extract conbody block
        conbody_pattern = re.compile(r"<conbody>.*?</conbody>", re.DOTALL)
        conbody_match = conbody_pattern.search(content)
        if conbody_match:
            conbody_block = conbody_match.group(0)
            content = conbody_pattern.sub("<!--CONBODY_PLACEHOLDER-->", content, 1)

        # Re-insert them in reversed order if they exist
        if shortdesc_match and conbody_match:
            content = content.replace("<!--SHORTDESC_PLACEHOLDER-->", conbody_block, 1)
            content = content.replace("<!--CONBODY_PLACEHOLDER-->", shortdesc_block, 1)

    return content

def introduce_error_empty_required_element(content):
    """
    Make <shortdesc></shortdesc> empty if present.
    """
    return re.sub(r"<shortdesc>.*?</shortdesc>", "<shortdesc></shortdesc>", content, flags=re.DOTALL)

def introduce_error_inconsistent_terminology(content):
    """
    Introduce a small mismatch in terminology: replace some 'click' with 'select'
    and vice versa, to create style inconsistencies.
    """
    # We'll force some 'click'/'select' text in the content:
    # Just append them at the end of the shortdesc or paragraphs to ensure they're there.
    # This is a naive approach.
    content += "\n<!-- Additional text: click the button, then select the menu. -->\n"

    # Swap one occurrence each
    content = content.replace("click", "select", 1)
    content = content.replace("select", "click", 1)
    return content

def generate_non_compliant_content(index):
    """
    Builds a 'base' DITA topic, then applies 1 to 3 random errors.
    """
    topic_type = random.choice(TOPIC_TYPES)
    doctype = DOCTYPE_MAP[topic_type]

    topic_id = f"{topic_type}_bad_{index}"
    title = fake.sentence(nb_words=5)
    shortdesc = fake.sentence(nb_words=8)
    body_paragraphs = [
        f"<p>{fake.paragraph(nb_sentences=2)}</p>",
        f"<p>{fake.paragraph(nb_sentences=2)}</p>"
    ]

    if topic_type == "task":
        task_body = f"""
        <taskbody>
            <steps>
                <step>
                    <cmd>Click the {fake.word()}</cmd>
                    <info>{fake.sentence(nb_words=5)}</info>
                </step>
                <step>
                    <cmd>Select the {fake.word()}</cmd>
                    <info>{fake.sentence(nb_words=5)}</info>
                </step>
            </steps>
        </taskbody>
        """
        body_content = task_body
    elif topic_type == "reference":
        ref_body = "\n        ".join(body_paragraphs)
        body_content = f"""
        <refbody>
            {ref_body}
        </refbody>
        """
    else:
        con_body = "\n        ".join(body_paragraphs)
        body_content = f"""
        <conbody>
            {con_body}
        </conbody>
        """

    base_content = f"""<?xml version="1.0" encoding="UTF-8"?>
{doctype}
<{topic_type} id="{topic_id}">
    <title>{title}</title>
    <shortdesc>{shortdesc}</shortdesc>
    {body_content}
</{topic_type}>
"""

    # Potential errors
    error_funcs = [
        introduce_error_missing_title,
        introduce_error_misspelled_root_tag,
        introduce_error_invalid_xml_syntax,
        introduce_error_missing_required_attribute,
        introduce_error_invalid_attribute_value,
        introduce_error_incorrect_element_order,
        introduce_error_empty_required_element,
        introduce_error_inconsistent_terminology
    ]

    # Decide how many errors (1 to 3) to introduce in this file
    num_errors = random.randint(1, 3)
    chosen_errors = random.sample(error_funcs, num_errors)

    mutated_content = base_content
    for err_func in chosen_errors:
        mutated_content = err_func(mutated_content)

    return mutated_content


# --------------------------------------------------------------------
# 3. File Creation Logic
# --------------------------------------------------------------------
def create_compliant_file(index):
    file_name = f"good_{index}.dita"
    content = generate_compliant_content(index)
    file_path = os.path.join(GOOD_FOLDER, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def create_non_compliant_file(index):
    file_name = f"bad_{index}.dita"
    content = generate_non_compliant_content(index)
    file_path = os.path.join(BAD_FOLDER, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    # Ensure folders exist
    os.makedirs(GOOD_FOLDER, exist_ok=True)
    os.makedirs(BAD_FOLDER, exist_ok=True)

    # Create 10 compliant files
    for i in range(1, 11):
        create_compliant_file(i)

    # Create 10 non-compliant files
    for i in range(1, 11):
        create_non_compliant_file(i)

    print("Done populating the sample_data folder with good and bad DITA files.")

if __name__ == "__main__":
    main()