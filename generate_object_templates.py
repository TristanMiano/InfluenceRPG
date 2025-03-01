#!/usr/bin/env python3
"""
generate_object_templates.py

This script searches the 'reference' directory for text-based materials,
reads each file, and uses the Gemini 2.0 Flash API (configured in config/llm_config.json)
to analyze the content. Gemini is prompted to recognize objects such as types of people,
professions, titles (military or noble), military hierarchy units (e.g., platoons, brigades),
ships, weapons, place names, vehicles, items, forts, towns, etc. For each file,
it returns a JSON array of object templates. The final output is saved in 'object_templates.json'.
"""

import os
import json
import argparse
from pathlib import Path

def load_config():
    """
    Loads Gemini configuration from config/llm_config.json.
    """
    config_path = Path("config") / "llm_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}

def traverse_reference_directory(ref_dir):
    """
    Walk through the reference directory and collect all text-based files.
    """
    ref_files = []
    for root, dirs, files in os.walk(ref_dir):
        for file in files:
            if file.endswith(('.txt', '.md')):
                ref_files.append(Path(root) / file)
    return ref_files

def read_file(file_path):
    """
    Reads the content of a file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def call_gemini_generate_json(prompt, config):
    """
    Calls the Gemini 2.0 Flash API using the google.genai package.
    If the API is unavailable, returns a simulated empty JSON array.
    """
    retries = 3  # Maximum number of retries on rate limit errors
    while retries > 0:
        try:
            from google import genai
            api_key = config.get("GEMINI_API_KEY")
            model = config.get("DEFAULT_MODEL", "gemini-2.0-flash")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=[prompt]
            )
            json_output = response.text.strip()
            # Clean up potential markdown formatting (e.g., ```json ... ```)
            if json_output.startswith("```json"):
                json_output = json_output[len("```json"):].strip()
            if json_output.endswith("```"):
                json_output = json_output[:-3].strip()
            return json_output
        except ImportError:
            print("Gemini API package not found. Simulating output.")
            json_output = "[]"
            return json_output
        except Exception as e:
            error_message = str(e).lower()
            # Check for rate limit error indicators: 429 status code or RESOURCE_EXHAUSTED keyword
            if "429" in error_message or "resource_exhausted" in error_message:
                print("Rate limit exceeded. Waiting 60 seconds before retrying...")
                import time
                time.sleep(60)
                retries -= 1
                continue  # Try the request again
            else:
                print("Error calling Gemini API:", e)
                json_output = "[]"
                return json_output


def generate_object_templates_for_file(content, file_path, config):
    """
    Constructs a prompt for Gemini to extract recognized objects from the content,
    then calls Gemini and parses the resulting JSON.
    """
    prompt = f"""
Analyze the following reference material extracted from the file: {file_path}.
Identify any objects that fall under these categories:
- Types of people, professions, titles (military or noble),
- Military hierarchy units (e.g., platoons, brigades),
- Ships, weapons, place names, vehicles, items, forts, towns, etc.
For each recognized object, output a JSON object with the following keys:
  - "category": the object category (e.g., "ship", "weapon", "town", etc.)
  - "name": the name of the object
  - "attributes": an object containing any additional details (if available)
Output the result as a JSON array. If no objects are found, output an empty JSON array.

Content:
\"\"\"{content}\"\"\"
"""
    json_output = call_gemini_generate_json(prompt, config)
    try:
        templates = json.loads(json_output)
    except json.JSONDecodeError:
        print(f"Failed to decode JSON output for file {file_path}.")
        print(json_output)
        templates = []
    return templates

def main():
    parser = argparse.ArgumentParser(
        description="Generate JSON templates for objects recognized in reference materials using Gemini 2.0 Flash."
    )
    parser.add_argument("--reference_dir", type=str, default="reference",
                        help="Directory containing reference materials.")
    parser.add_argument("--output", type=str, default="object_templates.json",
                        help="Output JSON file to store object templates.")
    args = parser.parse_args()

    # Load configuration for Gemini
    config = load_config()
    ref_dir = Path(args.reference_dir)
    ref_files = traverse_reference_directory(ref_dir)

    all_templates = {}

    for file_path in ref_files:
        print(f"Processing {file_path}...")
        content = read_file(file_path)
        if not content.strip():
            continue
        templates = generate_object_templates_for_file(content, file_path, config)
        all_templates[str(file_path)] = templates

    # Write the collected JSON templates to the output file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_templates, f, indent=2)
    print(f"Object templates generated and saved to {args.output}")

if __name__ == "__main__":
    main()
