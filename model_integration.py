# model_integration.py
import os
import json
from dotenv import load_dotenv
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Lazy import so demo still runs without openai package installed if key absent
OPENAI_AVAILABLE = False
if OPENAI_KEY:
    try:
        import openai
        openai.api_key = OPENAI_KEY
        OPENAI_AVAILABLE = True
    except Exception as e:
        OPENAI_AVAILABLE = False

def make_rationale(decision_id, recent_messages):
    """
    Produce a rationale for a decision: uses OpenAI if available, else a deterministic mock.
    recent_messages: list of dicts (last N messages) to include in the prompt.
    """
    if OPENAI_AVAILABLE:
        prompt = build_rationale_prompt(decision_id, recent_messages)
        resp = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=250,
            temperature=0.2,
            n=1
        )
        txt = resp.choices[0].text.strip()
        return {"decision_id": decision_id, "rationale": txt, "source": "openai"}
    else:
        # deterministic mock summary (safe for demo)
        text = f"Decision {decision_id}: Based on recent trends (exercise adherence ~50%, flagged lipid rise), trial supplement recommended to improve lipid profile and energy. Monitor at next 3-month panel. Confidence: medium."
        # include short list of messages excerpted
        excerpt = [m["text"] for m in recent_messages[-6:]]
        return {"decision_id": decision_id, "rationale": text, "messages_excerpt": excerpt, "source": "mock"}

def build_rationale_prompt(decision_id, recent_messages):
    # build a concise prompt for the LLM if using OpenAI
    msgs_text = "\n".join([f"{m['timestamp']} | {m['sender']}: {m['text']}" for m in recent_messages[-10:]])
    prompt = (
        f"You are a clinical assistant creating a concise rationale for decision {decision_id}.\n"
        "Use the recent message thread below and produce a short JSON with keys: decision_id, rationale, confidence_level.\n"
        "Keep rationale to 2-3 sentences.\n\n"
        f"Recent messages:\n{msgs_text}\n\nReturn only valid JSON."
    )
    return prompt
