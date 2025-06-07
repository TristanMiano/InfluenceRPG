import logging

try:
    import tiktoken
except ImportError:
    tiktoken = None

# Map model names to their max context window (in tokens)
_MODEL_CONTEXT_SIZES = {
    "gemini-2.0-flash": 131072,  # example: 128K-token window
    "gpt-3.5-turbo": 4096,
    "gpt-4": 8192,
    # add other models & windows as needed
}

logging.basicConfig(level=logging.INFO)


def get_encoding(model_name: str):
    """
    Return the tiktoken encoding for the given model, or a fallback.
    """
    if tiktoken:
        try:
            return tiktoken.encoding_for_model(model_name)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")
    raise RuntimeError("tiktoken is not installed")


def count_tokens(text: str, model_name: str) -> int:
    """
    Estimate tokens in `text` for `model_name`.
    Logs the count.
    """
    try:
        encoding = get_encoding(model_name)
        tokens = len(encoding.encode(text))
    except Exception:
        # fallback heuristic: 1 token ≈ 4 characters
        tokens = max(1, len(text) // 4)
    logging.info(f"[TokenCounter] count_tokens → {tokens} tokens for model '{model_name}'")
    return tokens


def get_model_max_tokens(model_name: str) -> int | None:
    """
    Return the maximum context window for `model_name`, if known.
    """
    return _MODEL_CONTEXT_SIZES.get(model_name)


def compute_usage_percentage(token_count: int, model_name: str) -> float:
    """
    Compute what percentage of the model's context window `token_count` uses.
    Logs the percentage.
    """
    max_tokens = get_model_max_tokens(model_name)
    if not max_tokens:
        logging.warning(f"[TokenCounter] Unknown max context size for model '{model_name}'")
        return 0.0
    pct = (token_count / max_tokens) * 100
    logging.info(f"[TokenCounter] context usage → {pct:.2f}% of {model_name} window")
    return pct


if __name__ == "__main__":
    # Quick test when run as a script
    sample_text = "Hello, this is a test message to count tokens."
    model = "gemini-2.0-flash"
    tok_count = count_tokens(sample_text, model)
    pct = compute_usage_percentage(tok_count, model)
    print(f"Tokens: {tok_count}, Usage: {pct:.2f}% of {model} window")
