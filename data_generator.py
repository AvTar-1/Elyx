# data_generator.py
"""
Generates an 8-month WhatsApp-style conversation JSON .
- Uses local Mistral via llama_cpp if available (set LLAMA_GGUF_PATH env var or default models/...).
- Enforces constraints: tests every ~90 days, ~5 member-initiated convos/week, fortnightly exercise updates,
  travel 1 week per 4, adherence ~50%, occasional clinical decisions.
Output:
  - data/messages.json
  - decisions/<decision_id>.json (rationales)
"""

import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import math
import sys
from typing import List, Dict, Any

# -------- CONFIG --------
START_DATE = datetime(2025, 1, 1)     # deterministic start date (change if you want)
DAYS = 8 * 30                         # approx 8 months (240 days)
OUT_DIR = Path("data")
OUT_PATH = OUT_DIR / "messages.json"
DECISIONS_DIR = OUT_DIR / "decisions"
SEED = None                             # change or None for non-deterministic runs
MEMBER = {
    "id": "rohan_patel_001",
    "name": "Rohan Patel",
    "age": 36,
    "location": "Singapore",
    "chronic_condition": "High LDL cholesterol"
}
MODEL_PATH = os.getenv("LLAMA_GGUF_PATH", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
USE_LLM = True                        # set to False to force template-only generation
LLM_N_THREADS = min(8, (os.cpu_count() or 4))
LLM_N_CTX = 2048

# Probabilities & rules
MEMBER_MSGS_PER_WEEK = 5.0            # average
MEMBER_MSG_DAILY_P = MEMBER_MSGS_PER_WEEK / 7.0
CLINICAL_DECISION_DAILY_P = 0.02     # chance of explicit clinical decision on a given day
ADHERENCE_PROB = 0.5                 # member sticks to plan ~50%
# ------------------------

if SEED is not None:
    random.seed(SEED)

OUT_DIR.mkdir(parents=True, exist_ok=True)
DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

# Attempt to import llama_cpp (local Mistral). If not available, graceful fallback.
_llm = None
if USE_LLM:
    try:
        from llama_cpp import Llama
        print("Initializing local Llama model... (this may take a moment)")
        _llm = Llama(model_path=MODEL_PATH, n_ctx=LLM_N_CTX, n_threads=LLM_N_THREADS)
        print("Local Llama initialized.")
    except Exception as e:
        print("Warning: Failed to initialize llama_cpp Llama. Falling back to template generator.")
        print("Error:", e)
        _llm = None

# Roles
ROLES = [
    {"sender": "Rohan", "sender_role": "member"},
    {"sender": "Ruby", "sender_role": "concierge"},
    {"sender": "Dr_Warren", "sender_role": "medical"},
    {"sender": "Advik", "sender_role": "coach"}
]

# Utility helpers
def next_id(counter=[0]):
    counter[0] += 1
    return counter[0]

def now_iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()

def safe_generate_text(prompt: str, max_tokens=120, temperature=0.6) -> str:
    """
    Try to generate with LLM. If unavailable or generation fails, return a simple template.
    This function returns a short WhatsApp-style single message (1-2 sentences).
    """
    # simple fallback template (choose a short sentence)
    def fallback():
        # pick a short template to match prompt context (look for sender names)
        if "Dr_Warren" in prompt:
            return "I've reviewed the results — mild change observed; we'll monitor and update the plan."
        if "Ruby" in prompt:
            return "Noted — we've scheduled the test and will share the results when available."
        if "Advik" in prompt:
            return "Here's your updated exercise plan for the next two weeks. Keep intensity moderate."
        if "Rohan" in prompt:
            return "Thanks — I completed today's session and felt better afterward."
        return "Thanks for the update — noted."

    if _llm is None:
        return fallback()

    try:
        resp = _llm(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        # llama_cpp returns choices list where text is in ['choices'][0]['text']
        text = ""
        try:
            text = resp["choices"][0].get("text", "")
        except Exception:
            # some builds may use 'message' or different shape; try fallback
            text = str(resp)
        text = text.strip()
        if not text:
            return fallback()
        # LLM may return multiple sentences - trim to 2 sentences max
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if not sentences:
            return fallback()
        short = ". ".join(sentences[:2])
        if not short.endswith("."):
            short += "."
        return short
    except Exception as e:
        print("LLM generation failed, fallback used. Error:", e, file=sys.stderr)
        return fallback()

# ------------ Message generation functions --------------
def generate_onboarding_messages(start_dt: datetime, msgs: list):
    # Ruby welcome
    msg = {
        "id": next_id(),
        "timestamp": now_iso(start_dt),
        "sender": "Ruby",
        "sender_role": "concierge",
        "text": safe_generate_text(f"Ruby onboarding message for {MEMBER['name']}", temperature=0.0),
        "tags": ["ONBOARD"],
        "decision_id": None,
        "message_type": "system",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": False}
    }
    msgs.append(msg)
    # Doctor initial plan
    msg2 = {
        "id": next_id(),
        "timestamp": now_iso(start_dt + timedelta(hours=1)),
        "sender": "Dr_Warren",
        "sender_role": "medical",
        "text": safe_generate_text(f"Dr_Warren initial plan for {MEMBER['name']}", temperature=0.0),
        "tags": ["PLAN"],
        "decision_id": None,
        "message_type": "system",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": False}
    }
    msgs.append(msg2)

def generate_test_schedule(test_dt: datetime, msgs: list, decision_prefix="decision_test"):
    # schedule
    decision_id = f"{decision_prefix}_{uuid.uuid4().hex[:8]}"
    m_sched = {
        "id": next_id(),
        "timestamp": now_iso(test_dt),
        "sender": "Ruby",
        "sender_role": "concierge",
        "text": safe_generate_text(f"Ruby schedule test for {MEMBER['name']} on {test_dt.date()}", temperature=0.0),
        "tags": ["TEST_SCHEDULE"],
        "decision_id": decision_id,
        "message_type": "system",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": False}
    }
    msgs.append(m_sched)
    # results next day
    res_dt = test_dt + timedelta(days=1, hours=9)
    m_res = {
        "id": next_id(),
        "timestamp": now_iso(res_dt),
        "sender": "Dr_Warren",
        "sender_role": "medical",
        "text": safe_generate_text(f"Dr_Warren test results for {MEMBER['name']} on {res_dt.date()}", temperature=0.0),
        "tags": ["TEST_RESULT"],
        "decision_id": decision_id,
        "message_type": "report",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": False}
    }
    msgs.append(m_res)
    # Optionally create a rationale file (deterministic temp)
    try:
        rationale_prompt = (
            f"[Rationale] Create a short JSON rationale for {decision_id} based on the test result: '{m_res['text']}'. "
            "Include keys: decision_id, rationale, confidence, next_steps."
        )
        rationale_text = safe_generate_text(rationale_prompt, temperature=0.0)
        try:
            # try to craft simple JSON for rationale
            rationale_obj = {
                "decision_id": decision_id,
                "rationale": rationale_text,
                "confidence": "medium",
                "next_steps": ["Monitor adherence", "Recheck at next 3-month panel"]
            }
            with open(DECISIONS_DIR / f"{decision_id}.json", "w", encoding="utf-8") as fh:
                json.dump(rationale_obj, fh, indent=2)
        except Exception as e:
            print("Failed to save rationale file:", e)
    except Exception as e:
        print("Rationale generation skipped:", e)

def generate_exercise_update(dt: datetime, msgs: list, week_index: int, travel_week=False):
    m = {
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=9)),
        "sender": "Advik",
        "sender_role": "coach",
        "text": safe_generate_text(f"Advik exercise update for week {week_index} (travel_week={travel_week})", temperature=0.1),
        "tags": ["EXERCISE_UPDATE"] if not travel_week else ["EXERCISE_UPDATE","TRAVEL_ADAPT"],
        "decision_id": None,
        "message_type": "plan",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": travel_week}
    }
    msgs.append(m)

def generate_member_status(dt: datetime, msgs: list, adherence_flag: bool, travel_week=False):
    # Member sends status message (adherence or not)
    if adherence_flag:
        tag = ["STATUS","ADHERENCE"]
    else:
        tag = ["STATUS","MISSED"]
    meta = {"member_initiated": True, "adherence_flag": adherence_flag, "travel_week": travel_week}
    # Build prompt hint
    prompt = f"Rohan status message. adherence={adherence_flag}. travel_week={travel_week}."
    text = safe_generate_text(prompt, temperature=0.5)
    m = {
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=18)),
        "sender": "Rohan",
        "sender_role": "member",
        "text": text,
        "tags": tag,
        "decision_id": None,
        "message_type": "chat",
        "meta": meta
    }
    msgs.append(m)
    # Optionally reply from Ruby
    if not adherence_flag:
        reply_text = safe_generate_text(f"Ruby supportive reply for missed adherence (day {dt.date()})", temperature=0.2)
        msgs.append({
            "id": next_id(),
            "timestamp": now_iso(dt + timedelta(hours=20)),
            "sender": "Ruby",
            "sender_role": "concierge",
            "text": reply_text,
            "tags": ["REPLY","SUPPORT"],
            "decision_id": None,
            "message_type": "chat",
            "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": travel_week}
        })

def generate_member_question(dt: datetime, msgs: list, travel_week=False):
    # Member-initiated question (scheduling/swap/ask)
    prompt = f"Rohan asks a question (scheduling/advice). travel_week={travel_week}"
    text = safe_generate_text(prompt, temperature=0.6)
    m = {
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=10 + random.randint(0,6))),
        "sender": "Rohan",
        "sender_role": "member",
        "text": text,
        "tags": ["QUESTION"],
        "decision_id": None,
        "message_type": "chat",
        "meta": {"member_initiated": True, "adherence_flag": None, "travel_week": travel_week}
    }
    msgs.append(m)
    # reply from appropriate staff (Advik or Ruby)
    responder = random.choice(["Advik", "Ruby"])
    reply_text = safe_generate_text(f"{responder} reply to member question", temperature=0.2)
    msgs.append({
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=11 + random.randint(0,4))),
        "sender": responder,
        "sender_role": "coach" if responder == "Advik" else "concierge",
        "text": reply_text,
        "tags": ["REPLY"],
        "decision_id": None,
        "message_type": "chat",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": travel_week}
    })

def generate_clinical_decision(dt: datetime, msgs: list):
    # Dr_Warren recommends something (supplement/med/referral)
    decision_id = f"decision_{uuid.uuid4().hex[:8]}"
    prompt = f"Dr_Warren creates a clinical decision for {MEMBER['name']} based on mild lipid rise and adherence patterns."
    text = safe_generate_text(prompt, temperature=0.0)
    msg = {
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=13)),
        "sender": "Dr_Warren",
        "sender_role": "medical",
        "text": text,
        "tags": ["DECISION"],
        "decision_id": decision_id,
        "message_type": "decision",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": False}
    }
    msgs.append(msg)
    # Save rationale JSON deterministically (temperature 0.0)
    rationale_prompt = (
        f"Create a JSON rationale for {decision_id}. Context: member adherence approx {ADHERENCE_PROB*100:.0f}% and "
        f"recent mild LDL rise. Return keys: decision_id, rationale, confidence, next_steps."
    )
    rationale_text = safe_generate_text(rationale_prompt, temperature=0.0)
    rationale_obj = {
        "decision_id": decision_id,
        "rationale": rationale_text,
        "confidence": "medium",
        "next_steps": ["Monitor labs", "Reinforce adherence", "Follow-up in 6 weeks"]
    }
    with open(DECISIONS_DIR / f"{decision_id}.json", "w", encoding="utf-8") as fh:
        json.dump(rationale_obj, fh, indent=2)

# ---------------- Main scheduler ----------------
def scheduler(start_date: datetime, days: int) -> Dict[str, Any]:
    msgs: List[Dict[str, Any]] = []
    generate_onboarding_messages(start_date, msgs)

    # compute weeks and travel weeks schedule up front
    total_weeks = math.ceil(days / 7)
    travel_weeks = set()
    # choose travel weeks deterministically: weeks 4,8,12,... (1-indexed)
    for w in range(1, total_weeks + 1):
        if w % 4 == 0:
            travel_weeks.add(w)

    # compute test days: day offsets 0, 90, 180 (within days)
    test_offsets = [0, 90, 180]
    # clip test offsets to range
    test_offsets = [d for d in test_offsets if d < days]

    # iterate days
    for day_offset in range(days):
        dt = start_date + timedelta(days=day_offset)
        week_index = (day_offset // 7) + 1
        travel_week = week_index in travel_weeks

        # fortnightly exercise update: every 14 days (we'll place on day 1 of each fortnight)
        if day_offset % 14 == 0:
            generate_exercise_update(dt, msgs, week_index, travel_week=travel_week)

        # schedule tests on specified offsets
        if day_offset in test_offsets:
            generate_test_schedule(dt, msgs)

        # member-initiated messages: approx ~5/week => daily Bernoulli with MEMBER_MSG_DAILY_P
        if random.random() < MEMBER_MSG_DAILY_P:
            # decide if it's a status or question
            if random.random() < 0.6:
                # status (adherence true/false based on ADHERENCE_PROB)
                adherence_flag = random.random() < ADHERENCE_PROB
                generate_member_status(dt, msgs, adherence_flag=adherence_flag, travel_week=travel_week)
            else:
                generate_member_question(dt, msgs, travel_week=travel_week)

        # occasional clinical decision events
        if random.random() < CLINICAL_DECISION_DAILY_P:
            generate_clinical_decision(dt, msgs)

        # small chance of a short staff-initiated proactive check in (Ruby)
        if random.random() < 0.1:
            msgs.append({
                "id": next_id(),
                "timestamp": now_iso(dt + timedelta(hours=9)),
                "sender": "Ruby",
                "sender_role": "concierge",
                "text": safe_generate_text(f"Ruby proactive check-in on {dt.date()}", temperature=0.2),
                "tags": ["CHECKIN"],
                "decision_id": None,
                "message_type": "chat",
                "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": travel_week}
            })

    # sort messages by timestamp and ensure unique sequential integer ids (reassign to tidy)
    msgs.sort(key=lambda m: m["timestamp"])
    for i, m in enumerate(msgs, start=1):
        m["id"] = i

    # compute basic meta statistics
    total_msgs = len(msgs)
    member_msgs = sum(1 for m in msgs if m["sender_role"] == "member")
    adherence_true = sum(1 for m in msgs if m["meta"].get("adherence_flag") is True)
    adherence_false = sum(1 for m in msgs if m["meta"].get("adherence_flag") is False)
    adherence_pct = (adherence_true / max(1, (adherence_true + adherence_false))) if (adherence_true + adherence_false) > 0 else None

    out = {
        "member": MEMBER,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": {"start_date": start_date.date().isoformat(), "days": days},
        "meta": {
            "total_messages": total_msgs,
            "member_messages": member_msgs,
            "estimated_member_messages_per_week": MEMBER_MSGS_PER_WEEK,
            "adherence_pct_observed": adherence_pct
        },
        "messages": msgs
    }
    return out

def write_output(obj: Dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
    print(f"Wrote {path} with {len(obj['messages'])} messages.")

# --------------- CLI ---------------
if __name__ == "__main__":
    print("Generating 8-month conversation for member:", MEMBER["name"])
    out = scheduler(START_DATE, DAYS)
    write_output(out, OUT_PATH)
    print("Decisions saved to:", DECISIONS_DIR.resolve())
    print("Generation complete.")
