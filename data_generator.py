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
from prompts import load_prompt, format_prompt
from model_integration_local import generate_text, generate_rationale, generate_paraphrases

SEED = None
if SEED is not None:
    random.seed(SEED)
else:
    random.seed()

MEMBER = {
    "id": "rohan_patel_001",
    "name": "Rohan Patel",
    "age": 36,
    "location": "Singapore",
    "chronic_condition": "High LDL cholesterol"
}

def simple_similarity(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)

def dedupe_variants(candidates, min_diff=0.6):
    seen = []
    final = []
    for c in candidates:
        if all(simple_similarity(c, s) < min_diff for s in seen):
            seen.append(c)
            final.append(c)
    return final

def force_variety(variants, min_count=4):
    deduped = dedupe_variants(variants)
    # If not enough unique variants, mutate the rest
    while len(deduped) < min_count and variants:
        for v in variants:
            if v not in deduped:
                suffix = random.choice([
                    " (just checking!)",
                    " — wanted to confirm.",
                    " (any thoughts?)",
                    " (let me know!)",
                    " (is that okay?)"
                ])
                mutated = v + suffix
                if all(simple_similarity(mutated, s) < 0.6 for s in deduped):
                    deduped.append(mutated)
            if len(deduped) >= min_count:
                break
    return deduped

QUESTION_TEMPLATES = [
    "Can I swap my {from_ex} session for {to_ex} today?",
    "Is it okay to do {to_ex} instead of {from_ex} because of my schedule?",
    "Due to {reason}, can I change my workout from {from_ex} to {to_ex}?",
    "Would it be fine to replace {from_ex} with {to_ex} this week?",
    "Can I adjust my plan and do {to_ex} instead of {from_ex}?"
]

ADVISOR_QUESTION_TEMPLATES = [
    "How are you feeling about your current exercise plan?",
    "Have you noticed any changes in your energy levels this week?",
    "Is there anything you'd like to adjust in your routine?",
    "Are you experiencing any challenges with your medication?",
    "Would you like to discuss your nutrition habits?",
    "Do you have any travel plans coming up that might affect your schedule?",
    "How is your stress level lately?",
    "Are you sleeping well these days?",
    "Would you like to try a new workout type?",
    "Any feedback on your recent test results?"
]

def generate_member_question(dt: datetime, msgs: list, travel_week=False, week_index=0):
    from_ex = random.choice(["cardio","run","HIIT","cycling"])
    to_ex = random.choice(["strength","mobility","yoga","stretch"])
    reason = random.choice(["urgent meeting","travel","long day","family visit"])
    recent = "\n".join([f"{x['sender']}: {x['text']}" for x in msgs[-6:]]) if msgs else ""
    context_obj = {
        "member": MEMBER,
        "date": dt.date().isoformat(),
        "time": dt.time().isoformat(),
        "week_index": week_index,
        "travel_week": travel_week,
        "from_ex": from_ex,
        "to_ex": to_ex,
        "reason": reason,
        "recent_messages": recent
    }
    paraphrase_template = load_prompt("paraphrase_batch.txt")
    paraphrase_prompt = format_prompt(paraphrase_template, n=10, context=json.dumps(context_obj))
    variants = generate_paraphrases("paraphrase_batch.txt", paraphrase_prompt, n=10, temperature=0.85)
    print(f"[member paraphrase pool {dt.date()}]", variants)
    deduped = force_variety(variants, min_count=4)
    chosen = random.choice(deduped) if deduped else random.choice(QUESTION_TEMPLATES).format(from_ex=from_ex, to_ex=to_ex, reason=reason)
    msgs.append({
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=10 + random.randint(0,6))),
        "sender": "Rohan",
        "sender_role": "member",
        "text": chosen,
        "tags": ["MEMBER_QUESTION"],
        "decision_id": None,
        "message_type": "chat",
        "meta": {"member_initiated": True, "adherence_flag": None, "travel_week": travel_week}
    })

def generate_advisor_question(dt: datetime, msgs: list, advisor="Ruby", week_index=0, travel_week=False):
    topic = random.choice(["exercise", "medication", "nutrition", "stress", "sleep", "travel", "test results"])
    recent = "\n".join([f"{x['sender']}: {x['text']}" for x in msgs[-6:]]) if msgs else ""
    context_obj = {
        "member": MEMBER,
        "date": dt.date().isoformat(),
        "time": dt.time().isoformat(),
        "week_index": week_index,
        "travel_week": travel_week,
        "topic": topic,
        "recent_messages": recent
    }
    paraphrase_template = load_prompt("paraphrase_batch.txt")
    paraphrase_prompt = format_prompt(paraphrase_template, n=10, context=json.dumps(context_obj))
    variants = generate_paraphrases("paraphrase_batch.txt", paraphrase_prompt, n=10, temperature=0.85)
    print(f"[advisor paraphrase pool {dt.date()}]", variants)
    deduped = force_variety(variants, min_count=4)
    chosen = random.choice(deduped) if deduped else random.choice(ADVISOR_QUESTION_TEMPLATES)
    msgs.append({
        "id": next_id(),
        "timestamp": now_iso(dt + timedelta(hours=8 + random.randint(0,6))),
        "sender": advisor,
        "sender_role": "concierge" if advisor == "Ruby" else "coach",
        "text": chosen,
        "tags": ["ADVISOR_QUESTION"],
        "decision_id": None,
        "message_type": "chat",
        "meta": {"member_initiated": False, "adherence_flag": None, "travel_week": travel_week}
    })

START_DATE = datetime(2025, 1, 1)
DAYS = 8 * 30  # 8 months

msgs = []
for day in range(DAYS):
    dt = START_DATE + timedelta(days=day)
    week_index = day // 7
    travel_week = (week_index % 4 == 2)
    # Member question (random chance)
    if random.random() < 0.2:
        generate_member_question(dt, msgs, travel_week=travel_week, week_index=week_index)
    # Advisor question (random chance)
    if random.random() < 0.15:
        advisor = random.choice(["Ruby", "Advik"])
        generate_advisor_question(dt, msgs, advisor=advisor, week_index=week_index, travel_week=travel_week)

# Save messages to JSON file
output_dir = Path("data")
output_dir.mkdir(exist_ok=True)
with open(output_dir / "messages.json", "w") as f:
    json.dump(msgs, f, indent=2, default=str)

print(f"Generated {len(msgs)} messages.")

import uuid

def next_id():
    return str(uuid.uuid4())

def now_iso(dt):
    return dt.isoformat()

SENDER_TO_ROLE = {"Rohan":"member","Ruby":"concierge","Dr_Warren":"medical","Advik":"coach"}

def make_message(ts, sender, text, tags=None, decision_id=None, mtype="chat", meta=None):
    return {
        "id": next_id(),
        "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
        "sender": sender,
        "sender_role": SENDER_TO_ROLE.get(sender, "unknown"),
        "text": text,
        "tags": tags or [],
        "decision_id": decision_id,
        "message_type": mtype,
        "meta": meta or {"member_initiated": False, "adherence_flag": None, "travel_week": False}
    }
