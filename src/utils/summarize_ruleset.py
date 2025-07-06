#!/usr/bin/env python3
"""
summarize_ruleset.py — with NONE token handling and path fix

Usage:
  python -m src.utils.summarize_ruleset --ruleset-id <RULESET_ID>

This script reads the stored ruleset_chunks for the given ruleset,
summarizes each chunk (focusing strictly on game mechanics) with a per-chunk
token budget of (1_000_000 / (2 * num_chunks)), and updates the
rulesets.summary field with the combined result.
"""

import os
import sys
import argparse

# Ensure 'src' is on the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.db.ruleset_db import list_chunks, set_summary
from src.llm.llm_client import generate_completion, GEMINI_AVAILABLE
from src.utils.prompt_loader import load_prompt_template

# Local summarizer fallback if Gemini unavailable
local_summarizer = None
if not GEMINI_AVAILABLE:
    print("Gemini not available. Using local summarizer.")
    try:
        from transformers import pipeline
        local_summarizer = pipeline("summarization")
    except ImportError:
        local_summarizer = None

def summarize_text_locally(text: str, max_length: int):
    """Use HF pipeline if available, else just truncate."""
    if local_summarizer:
        out = local_summarizer(text, max_length=max_length, min_length=10, do_sample=False)
        return out[0]['summary_text']
    return text[: max_length * 4]  # fallback

def summarize_ruleset(ruleset_id: str):
    chunks = list_chunks(ruleset_id)
    if not chunks:
        print(f"No chunks found for ruleset {ruleset_id}")
        return

    n = len(chunks)
    max_tokens = int(1_000_000 / (2 * n))
    print(f"Summarizing {n} chunks at ≤{max_tokens} tokens each.")

    all_summaries = []
    for c in chunks:
        idx, text = c["chunk_index"], c["chunk_text"]
        if GEMINI_AVAILABLE:
            template = load_prompt_template("ruleset_summarization.txt")
            prompt = template.format(max_tokens=max_tokens, text=text)
            summary = generate_completion(prompt).strip()
        else:
            max_chars = max_tokens * 4
            summary = summarize_text_locally(text, max_length=max_chars).strip()

        if summary.upper() == "NONE":
            print(f" → chunk {idx} yielded NONE, skipping.")
            continue

        print(f" → chunk {idx}: {len(summary)} chars")
        all_summaries.append(summary)

    full_summary = "\n\n".join(all_summaries) if all_summaries else ""
    set_summary(ruleset_id, full_summary)
    print(f"[DONE] ruleset.summary updated ({len(full_summary)} chars).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ruleset-id", required=True, help="UUID of the ruleset")
    args = parser.parse_args()
    summarize_ruleset(args.ruleset_id)

