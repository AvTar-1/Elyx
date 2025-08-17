# validate_messages.py
import json
from pathlib import Path
DATA_PATH = Path("data/messages.json")
doc = json.loads(DATA_PATH.read_text(encoding="utf-8"))
msgs = doc.get("messages", [])
bad = []
for i, m in enumerate(msgs, start=1):
    if "sender_role" not in m:
        bad.append((i, m.get("sender"), m.get("text")[:80]))
if bad:
    print("Messages missing sender_role:")
    for idx, sender, text in bad:
        print(idx, sender, text)
else:
    print("All messages have sender_role.")
