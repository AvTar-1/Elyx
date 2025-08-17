# model_integration_local.py
import os
import json
from llama_cpp import Llama
from typing import List, Dict, Any
from prompts import log_prompt_usage

MODEL_PATH = os.getenv("LLAMA_GGUF_PATH", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
N_CTX = int(os.getenv("LLM_N_CTX", "2048"))
N_THREADS = int(os.getenv("LLM_N_THREADS", "8"))

# Initialize model once
_llm = Llama(model_path=MODEL_PATH, n_ctx=N_CTX, n_threads=N_THREADS,seed=None)


def _log_and_call(prompt_name: str, prompt_text: str, meta: dict):
    # record the prompt for reproducibility
    log_prompt_usage(prompt_name, prompt_text, meta)
    # do the call and return raw response dict
    resp = _llm(prompt=prompt_text, max_tokens=meta.get("max_tokens", 200), temperature=meta.get("temperature", 0.2))
    return resp

def generate_text(prompt, temperature=0.9, max_tokens=128):
    output = _llm(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.95,
        top_k=50,
        repeat_penalty=1.2,
        seed=None,  # crucial!
        stop=["</s>"]
    )
    return output["choices"][0]["text"].strip()

def generate_paraphrases(prompt_name: str, prompt_text: str, n: int=6, temperature: float=0.7, max_tokens: int=512) -> List[str]:
    """
    Ask the model to return a JSON array of n paraphrases. The caller should pass a prompt that
    requests a JSON array. We parse and return a list of strings.
    """
    meta = {"temperature": 1, "max_tokens": max_tokens, "n_variants": n, "model_path": MODEL_PATH}
    resp = _log_and_call(prompt_name, prompt_text, meta)
    raw = ""
    try:
        raw = resp["choices"][0]["text"].strip()
    except Exception:
        raw = str(resp)
    # try to parse JSON array first
    try:
        arr = json.loads(raw)
        if isinstance(arr, list):
            return [str(x).strip() for x in arr]
    except Exception:
        # fallback: split lines, bullets, etc.
        lines = [ln.strip(" -•\t\n\r") for ln in raw.splitlines() if ln.strip()]
        # minimal sanitization and return up to n
        out = []
        for ln in lines:
            if len(ln) > 3:
                out.append(ln)
            if len(out) >= n:
                break
        if out:
            return out
    # ultimate fallback: return raw as single entry
    return [raw] if raw else []

def generate_rationale(prompt_name: str, prompt_text: str, temperature: float=0.0, max_tokens: int=300) -> Dict[str,Any]:
    """Return parsed JSON if model returns JSON, else a safe dict with raw text."""
    meta = {"temperature": temperature, "max_tokens": max_tokens, "model_path": MODEL_PATH}
    resp = _log_and_call(prompt_name, prompt_text, meta)
    raw = ""
    try:
        raw = resp["choices"][0]["text"].strip()
    except Exception:
        raw = str(resp)
    # attempt JSON parse
    try:
        parsed = json.loads(raw)
        return parsed
    except Exception:
        return {"raw": raw, "note": "could_not_parse_json"}
