import json
from collections import defaultdict
from pathlib import Path

def structure_reference_data(unstructured_path: Path, output_path: Path):
    # Load the unstructured JSON data
    with open(unstructured_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Flatten all object templates from all file keys into one list
    all_templates = []
    for file_key in data:
        all_templates.extend(data[file_key])

    # Remove duplicates based on (category, name), ignoring case and whitespace
    seen = set()
    unique_templates = []
    for template in all_templates:
        category = template.get("category", "").strip().lower()
        name = template.get("name", "").strip().lower()
        identifier = (category, name)
        if identifier not in seen:
            seen.add(identifier)
            unique_templates.append(template)

    # Organize templates by category
    organized = defaultdict(list)
    for template in unique_templates:
        cat = template.get("category", "").strip()
        organized[cat].append({
            "name": template.get("name", "").strip(),
            "attributes": template.get("attributes", {})
        })

    # Optionally, sort each category's list alphabetically by name
    for cat in organized:
        organized[cat] = sorted(organized[cat], key=lambda x: x["name"].lower())

    # Write the organized data to the output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(organized, f, indent=2)

if __name__ == "__main__":
    # Define paths (adjust as necessary)
    unstructured_file = Path("./unstructured/object_templates.json")
    structured_file = Path("./structured/references_structured.json")
    
    structure_reference_data(unstructured_file, structured_file)
    print(f"Structured references written to: {structured_file}")
