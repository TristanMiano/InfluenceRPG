from pathlib import Path

# Templates now live under the src package
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "prompt_templates"

def load_prompt_template(name: str) -> str:
    path = TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")
