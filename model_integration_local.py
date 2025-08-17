# model_integration_local.py
from llama_cpp import Llama
import os

MODEL_PATH = os.getenv("LLAMA_GGUF_PATH", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
_llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=8)

def build_prompt(decision_id, recent_messages):
    msgs_text = "\n".join([f"{m['timestamp']} | {m['sender']}: {m['text']}" for m in recent_messages])
    return f"""<s>[INST] You are a clinical assistant. 
Use the thread below to explain decision {decision_id}. 
Return JSON with keys: decision_id, rationale (2-3 sentences), confidence (low/medium/high), next_steps (list).
Messages:
{msgs_text}
[/INST]"""

def make_rationale(decision_id, recent_messages):
    prompt = build_prompt(decision_id, recent_messages)
    resp = _llm(prompt=prompt, max_tokens=200, temperature=0.0)
    return {"decision_id": decision_id, "raw": resp['choices'][0]['text'].strip(), "source": "local_mistral"}
