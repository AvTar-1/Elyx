# prompts.py
import json
from pathlib import Path
from collections import ChainMap
from datetime import datetime
import os

PROMPTS_DIR = Path("prompts")
LOG_DIR = Path("prompts/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG = LOG_DIR / "prompt_usage.jsonl"

def load_prompt(name: str) -> str:
    """
    Load a prompt file from prompts/<name>.txt (or .md).
    """
    p = PROMPTS_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"Prompt file not found: {p}")
    return p.read_text(encoding="utf-8")

class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"

def format_prompt(prompt_template: str, **kwargs) -> str:
    """
    Safely format a prompt template using {placeholders}.
    Unknown placeholders are left as-is (so formatting won't crash).
    """
    safe = SafeDict(**kwargs)
    return prompt_template.format_map(safe)

def log_prompt_usage(prompt_name: str, rendered_prompt: str, metadata: dict):
    """
    Append a JSON line to prompts/logs/prompt_usage.jsonl recording exact prompt and metadata.
    Metadata should include model, temperature, seed, caller (file/func) etc.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat()+"Z",
        "prompt_name": prompt_name,
        "prompt": rendered_prompt,
        "meta": metadata
    }
    with open(USAGE_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
