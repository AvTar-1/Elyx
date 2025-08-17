# app.py (improved, more robust)
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import traceback

# Import the generator so we can regenerate if file missing/corrupt
try:
    import data_generator
except Exception:
    data_generator = None

st.set_page_config(page_title="Elyx — Member Journey", layout="wide")
DATA_PATH = Path("data/messages.json")

def load_data():
    """
    Attempt to read and parse DATA_PATH. If missing/invalid, try regenerate (if generator available).
    Returns parsed JSON (dict) or raises Exception.
    """
    if not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0:
        st.warning(f"{DATA_PATH} is missing or empty.")
        if data_generator:
            st.info("Attempting to regenerate messages.json using data_generator.py ...")
            try:
                data_generator.main()
            except Exception as e:
                raise RuntimeError(f"data_generator failed: {e}")
        else:
            raise FileNotFoundError(f"{DATA_PATH} missing and data_generator module not available.")
    # At this point file should exist and be non-empty
    text = DATA_PATH.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try to give helpful debug info
        snippet = text[:400].replace("\n", "\\n")
        raise ValueError(f"JSON decode error: {e}. File starts with: {snippet}")

# UI
st.title("Elyx — Member Journey (Robust Debug Version)")

try:
    data = load_data()
except Exception as e:
    st.error("Failed to load data/messages.json.")
    st.exception(e)
    st.markdown("**Fix options:**\n\n"
                "- Make sure you ran `python data_generator.py` in the same folder.\n"
                "- Ensure `data/messages.json` contains valid JSON (not empty).\n"
                "- If you want me to regenerate now, click the button below.")
    if st.button("Try regenerate now"):
        if data_generator:
            try:
                data_generator.main()
                st.success("Regenerated data/messages.json — please restart the app (Streamlit will usually auto-reload).")
            except Exception as e2:
                st.error(f"Regeneration failed: {e2}")
                st.text(traceback.format_exc())
        else:
            st.error("data_generator.py not importable. Make sure file exists and is correct.")
    st.stop()

member = data.get("member", {})
messages = data.get("messages", [])

# If we reach here, data loaded successfully
st.sidebar.subheader("Member Snapshot")
st.sidebar.write(member)

st.subheader(f"Timeline for {member.get('name','(unknown)')}")
# simple listing
for m in messages[:200]:  # first 200 messages for fast rendering
    ts = datetime.fromisoformat(m["timestamp"])
    with st.expander(f"{ts.strftime('%Y-%m-%d %H:%M')} — {m['sender']} — {m.get('tags',[])}"):
        st.write(m["text"])
        if m.get("decision_id"):
            if st.button(f"Explain {m['decision_id']}", key=f"exp_{m['id']}"):
                # naive slice for local demo
                idx = next((i for i,x in enumerate(messages) if x["id"] == m["id"]), None)
                recent = messages[max(0, idx-12): idx+1] if idx is not None else messages[-12:]
                # On purpose we import local function from model_integration if present.
                try:
                    from model_integration import make_rationale
                    rationale = make_rationale(m["decision_id"], recent)
                    st.markdown("**Rationale**")
                    st.json(rationale)
                except Exception as e:
                    st.error("Rationale generation failed or model_integration not available.")
                    st.exception(e)
