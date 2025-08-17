# data_generator.py
import json
import random
from datetime import datetime, timedelta
import os

random.seed(42)

# Member profile from PDF (brief)
MEMBER = {
    "name": "Rohan Patel",
    "age": 36,
    "location": "Singapore",
    "id": "rohan_patel_001"
}

START_DATE = datetime(2025, 1, 1)   # choose static start date so demo is deterministic
DAYS = 8 * 30  # approx 8 months
OUT_PATH = "data/messages.json"

ROLES = [
    {"role": "Rohan", "type": "member"},
    {"role": "Ruby", "type": "concierge"},
    {"role": "Dr_Warren", "type": "medical"},
    {"role": "Advik", "type": "coach"}
]

def add_msg(msgs, dt, sender, text, tags=None, decision_id=None):
    msg = {
        "id": len(msgs)+1,
        "timestamp": dt.isoformat(),
        "sender": sender,
        "text": text,
        "tags": tags or [],
        "decision_id": decision_id
    }
    msgs.append(msg)
    return msg

def scheduler():
    msgs = []
    current = START_DATE
    week = 0
    decision_counter = 0

    # Insert initial onboarding messages
    add_msg(msgs, current, "Ruby", f"Hi {MEMBER['name']}, welcome to Elyx! We'll check-in regularly.", tags=["ONBOARD"])
    add_msg(msgs, current + timedelta(hours=1), "Dr_Warren", "Initial medical plan prepared. Baseline tests scheduled.", tags=["PLAN"])

    # Scheduler iterate days
    for day_offset in range(DAYS):
        dt = START_DATE + timedelta(days=day_offset)
        # weekly schedule logic
        if day_offset % 7 == 0:
            week += 1
            # every 2 weeks -> exercise update
            if week % 2 == 0:
                add_msg(msgs, dt + timedelta(hours=9), "Advik", f"Exercise plan updated for week {week}. Focus: mobility and strength.", tags=["PLAN_UPDATE"])
            # travel 1 week per 4 -> mark entire week as travel if week%4==0: create a travel note on day 1
            if week % 4 == 0:
                add_msg(msgs, dt + timedelta(hours=8), "Ruby", "Noted upcoming travel this week. We'll adapt your schedule.", tags=["TRAVEL"])

        # member-initiated messages: avg 5/week -> approx 0.714 per day: sample Bernoulli
        if random.random() < (5/7):
            # choose member message type
            mtype = random.choice(["question", "status", "log"])
            if mtype == "question":
                add_msg(msgs, dt + timedelta(hours=10), "Rohan", "Quick question about today's plan — can I swap cardio for strength?", tags=["QUESTION"])
                # reply from Advik
                add_msg(msgs, dt + timedelta(hours=11), "Advik", "Yes, swapping is fine — keep intensity moderate.", tags=["REPLY"])
            elif mtype == "status":
                adherence = random.choice([True, False]) if random.random() < 0.5 else False
                if adherence:
                    add_msg(msgs, dt + timedelta(hours=19), "Rohan", "Completed today's exercises as planned. Feeling good.", tags=["STATUS"])
                else:
                    add_msg(msgs, dt + timedelta(hours=20), "Rohan", "Missed exercise today, had a long meeting.", tags=["STATUS"])
                    add_msg(msgs, dt + timedelta(hours=22), "Ruby", "No worries — small steps tomorrow. Shall I nudge you 30 mins earlier?", tags=["REPLY"])

        # scheduled diagnostic panels at months 0, 3, 6 (approx days 0, 90, 180)
        if day_offset in (0, 90, 180):
            decision_counter += 1
            test_text = f"Diagnostic panel scheduled for {dt.date()}. Phlebotomy arranged."
            add_msg(msgs, dt + timedelta(hours=9), "Ruby", test_text, tags=["TEST_SCHEDULE"], decision_id=f"decision_test_{decision_counter}")
            # results posted a day later
            add_msg(msgs, dt + timedelta(days=1, hours=10), "Dr_Warren", "Panel results: minor lipid rise; will monitor and adjust plan.", tags=["TEST_RESULT"], decision_id=f"decision_test_{decision_counter}")

        # small chance of a clinical decision (e.g., med or referral)
        if random.random() < 0.02:
            decision_counter += 1
            add_msg(msgs, dt + timedelta(hours=13), "Dr_Warren", f"Recommend trial of supplement X for 6 weeks.", tags=["DECISION"], decision_id=f"decision_{decision_counter}")
            # Rationale placeholder: real rationale will be produced by LLM integration
            add_msg(msgs, dt + timedelta(hours=14), "Ruby", "Noted. Will update plan and monitor adherence.", tags=["ACTION"])

    # sort by timestamp to be sure
    msgs.sort(key=lambda m: m["timestamp"])
    return {"member": MEMBER, "messages": msgs}

def main():
    os.makedirs("data", exist_ok=True)
    out = scheduler()
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {OUT_PATH} with {len(out['messages'])} messages.")

if __name__ == "__main__":
    main()
