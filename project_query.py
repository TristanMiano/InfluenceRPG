import os
import json
import argparse
import tiktoken
import random

# Load configuration from config/config.json
def load_config():
    config_path = os.path.join("config", "llm_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}

# Initialize tiktoken encoder (using a common encoding; adjust as needed)
ENCODING = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    """Count tokens in text using tiktoken."""
    return len(ENCODING.encode(text))

# Define a prompt template that includes background information
PROMPT_TEMPLATE = """
Project Background:
This project is an ambitious tabletop role-playing game that integrates high-level strategic simulation with AI-based procedural generation. The system is designed to manage dynamic narratives, large-scale battles (including land, sea, and air engagements), and detailed management of characters, organizations, and events. By leveraging a robust simulation engine alongside AI-powered narrative generation, the project aims to produce a living world where every decision is enriched with context-specific storytelling.

User Query:
{user_prompt}
"""

def build_prompt_header(user_prompt):
    """Construct the full prompt header using the template."""
    return PROMPT_TEMPLATE.format(user_prompt=user_prompt).strip() + "\n\n"

def gemini_assess_file(content, user_prompt, config):
    """
    Calls the Gemini API via the google.genai package to determine if the entire file is relevant or should be summarized.
    
    The prompt instructs the model as follows:
      - If the whole file is relevant, respond exactly with "RELEVANT".
      - Otherwise, respond with "SUMMARY: {your summary}".
    
    Returns:
        A tuple (decision, processed_text) where:
          - decision is "include_whole" if the file should be included in full,
            or "summarize" if a summary is provided.
          - processed_text is None for "include_whole" or contains the summary text for "summarize".
    """
    # Retrieve API key and model from config or environment
    api_key = config.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    model = config.get("DEFAULT_MODEL", "gemini-2.0-flash")
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except ImportError:
        print("Gemini API package not found. Gemini provider will be disabled.")
        # Fallback: decide based on length (this is a simple fallback behavior)
        if len(content.split()) > 300:
            return ("summarize", content[:1000])
        else:
            return ("include_whole", None)
    
    # Build the prompt with clear instructions.
    prompt = (
        f"{user_prompt}\n\n"
        "You are an expert content analyzer for a complex technical project. Read the following content, and compare the content to the user query:\n\n"
        f"{content}\n\n"
        "If the entire file is relevant to the user query and should be included in full, respond with exactly 'RELEVANT'. "
        "Otherwise, if the file is too long or contains information that is better summarized, "
        "provide a brief summary. Your response must begin with 'SUMMARY:' followed by your summary in a few sentences."
    )
    retries = 3  # Maximum number of retries on rate limit errors
    while retries > 0:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[prompt]
            )
            result_text = response.text.strip()
            
            if result_text.upper().startswith("RELEVANT"):
                return ("include_whole", None)
            elif result_text.upper().startswith("SUMMARY:"):
                summary = result_text[len("SUMMARY:"):].strip()
                return ("summarize", summary)
            else:
                print("Unexpected Gemini response:", result_text)
                return ("summarize", content[:1000])
        except Exception as e:
            error_message = str(e).lower()
            # Check for rate limit error indicators: 429 status code or RESOURCE_EXHAUSTED keyword
            if "429" in error_message or "resource_exhausted" in error_message:
                logging.warning("Rate limit exceeded. Waiting 60 seconds before retrying...")
                time.sleep(60)
                retries -= 1
                continue  # Try the request again
            else:
                print("Error calling Gemini API:", e)
                return ("summarize", content[:1000])
        
# Example integration into our file processing logic
def model_assess_file(content, prompt, config):
    """
    Uses the Gemini API to decide whether to include the whole file or summarize it.
    The 'prompt' parameter can be used to inject additional context if needed.
    """
    decision, processed_content = gemini_assess_file(content, prompt, config)
    return decision, processed_content

def process_file(file_path, user_prompt, config):
    """
    Reads a file, assesses its relevance using Gemini, and returns its processed content with a header.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    decision, processed_content = model_assess_file(content, user_prompt, config)
    if decision == "skip":
        return None

    header = f"--- File: {file_path} ---\n"
    if decision == "include_whole":
        return header + content + "\n\n"
    elif decision == "summarize":
        return header + processed_content + "\n\n"
    else:
        # In case of unexpected decision, fallback to summarizing.
        return header + content[:1000] + "\n\n"


def traverse_and_collect(directory, user_prompt, token_limit, config):
    """
    Traverses the given directory, processes files based on relevance, and appends their content
    (prefaced with a detailed prompt header) until the token limit is reached.
    """
    prompt_header = build_prompt_header(user_prompt)
    collected_text = prompt_header
    token_count = count_tokens(collected_text)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_text = process_file(file_path, user_prompt, config)
            if file_text is None:
                continue
            new_tokens = count_tokens(file_text)
            if token_count + new_tokens > token_limit:
                print("Token limit reached. Stopping collection.")
                return collected_text
            collected_text += file_text
            token_count += new_tokens

    return collected_text

def main():
    parser = argparse.ArgumentParser(
        description="Attach a prompt header and collect relevant project text within a token limit."
    )
    parser.add_argument("--directory", type=str, default=".", help="Directory to traverse.")
    parser.add_argument("--prompt", type=str, required=True, 
                        help="User prompt (e.g., 'Find all files relevant to constructing large scale land battles.')")
    parser.add_argument("--token_limit", type=int, default=100000, 
                        help="Maximum number of tokens allowed in the output.")
    args = parser.parse_args()

    config = load_config()
    output_text = traverse_and_collect(args.directory, args.prompt, args.token_limit, config)
    print("=== OUTPUT ===")
    print(output_text)

if __name__ == "__main__":
    main()
