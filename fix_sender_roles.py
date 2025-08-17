# fix_sender_roles.py
import json
from pathlib import Path

DATA_PATH = Path("data/messages.json")
if not DATA_PATH.exists():
    print("data/messages.json not found.")
    raise SystemExit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    doc = json.load(f)

messages = doc.get("messages", [])
mapping = {
    "Rohan": "member",
    "Ruby": "concierge",
    "Dr_Warren": "medical",
    "Advik": "coach",
    "Advik": "coach",
    # add any other role-name -> role mapping your project uses
}

fixed = 0
for m in messages:
    if "sender_role" not in m or m.get("sender_role") in (None, ""):
        sender = m.get("sender", "")
        default_role = mapping.get(sender, "unknown")
        m["sender_role"] = default_role
        fixed += 1

if fixed:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"Patched {fixed} messages with missing sender_role and wrote {DATA_PATH}")
else:
    print("No missing sender_role fields found.")
