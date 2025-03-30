#!/usr/bin/env python3
"""
llm_client.py - Generic LLM Client for Chat Completions

This module loads LLM configuration from config/llm_config.json and provides a function
to generate completions using the Gemini API (or a simulated response if the API is unavailable).
It supports chat completions by accepting an optional conversation context parameter.
"""

import json
import time
from pathlib import Path

# Attempt to import the Gemini API client.
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def load_llm_config() -> dict:
    """
    Load LLM configuration settings from config/llm_config.json.

    Returns:
        dict: A dictionary containing the configuration settings.
    """
    config_path = Path("config") / "llm_config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}

def generate_completion(prompt: str, conversation_context: str = "", max_retries: int = 3) -> str:
    """
    Generate a completion using the Gemini API (or a simulated response) based on the provided prompt.
    For chat completions, the conversation context (e.g., the full chat history) can be prepended to the prompt.

    Args:
        prompt (str): The primary prompt text.
        conversation_context (str, optional): Full conversation context for chat completions.
                                              Defaults to an empty string.
        max_retries (int, optional): Maximum number of retries on rate limit errors. Defaults to 3.

    Returns:
        str: The generated completion text.
    """
    config = load_llm_config()
    api_key = config.get("GEMINI_API_KEY", "")
    model = config.get("DEFAULT_MODEL", "gemini-2.0-flash")
    
    # Combine conversation context and the prompt.
    full_prompt = f"{conversation_context}\n\n{prompt}" if conversation_context else prompt

    # If the Gemini API client is available, use it.
    if GEMINI_AVAILABLE:
        retries = max_retries
        while retries > 0:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model,
                    contents=[full_prompt]
                )
                completion_text = response.text.strip()
                return completion_text
            except Exception as e:
                error_message = str(e).lower()
                if "429" in error_message or "resource_exhausted" in error_message:
                    print("Rate limit exceeded, waiting before retrying...")
                    time.sleep(60)
                    retries -= 1
                    continue
                else:
                    print(f"Error calling Gemini API: {e}")
                    return ""
        # If retries are exhausted, return an empty string.
        return ""
    else:
        # Simulate a response if Gemini is not available.
        time.sleep(1)  # Simulate API delay.
        simulated_response = f"Simulated response for prompt:\n{full_prompt}"
        return simulated_response

if __name__ == "__main__":
    # Test block for generating a chat completion.
    conversation_history = (
        "User: Hi, what is our current mission?\n"
        "GM: Our mission is to secure the perimeter."
    )
    prompt = "User: What's our next move?"
    completion = generate_completion(prompt, conversation_context=conversation_history)
    print("Generated Completion:")
    print(completion)
