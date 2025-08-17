# 🚀 Elyx Hackathon – Data Generator  

This project generates an **8-month WhatsApp-style conversation dataset** for the Elyx health platform.  
It simulates realistic interactions between a member (**Rohan Patel**) and advisors (**Ruby, Dr_Warren, Advik**), including onboarding, medical plans, test scheduling, exercise updates, travel, adherence, and Q&A.  

---
## Tech_Architecture:

+------------------+       +-------------------------+
|   Streamlit UI   | <---> |   data_generator.py     |
|  (app.py)        |       |  (message + rationale)  |
+------------------+       +-------------------------+
           |                           |
           v                           v
+------------------+         +----------------------+
|  model_integration| -----> |   Local LLM (Mistral)|
|  (llama_cpp API) |         |   GGUF Quantized     |
+------------------+         +----------------------+
           |
           v
+-------------------+
|  JSON Outputs     |
|  (messages +      |
|   decisions)      |
+-------------------+

---

## ⚡ Quick Start  

1. **Clone the repository:**  
   ```bash
   git clone https://github.com/AvTar-1/Elyx.git
   cd Elyx
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app:**

   ```bash
   streamlit run app.py
   ```

---

## ✨ Features

* 🤖 **Local LLM Integration**: Runs on **Mistral-7B** via `llama_cpp`
* 🧩 **Rich Context**: Each message considers date, week, travel, and past context
* 🎲 **Randomized Conversations**: Member and advisor questions are diverse and deduplicated
* 🩺 **Clinical Realism**: Plans, tests, and decisions appear at realistic intervals
* 📂 **Structured Outputs**:

  * `data/messages.json` → Full conversation timeline
  * `decisions/<id>.json` → Clinical rationale for each decision

---

## 📊 Example Timeline

```
2025-01-01 00:00 — Ruby — tags: [ONBOARD]
Hi Rohan Patel, welcome to Elyx! We'll check-in regularly.

2025-01-01 01:00 — Dr_Warren — tags: [PLAN]
Initial medical plan prepared. Baseline tests scheduled.

2025-01-02 08:30 — Advik — tags: [EXERCISE]
Don’t forget your morning walk today. 15 minutes is a great start!
```

---

## 🛠️ Tech Stack

* 🎨 **Frontend**: Streamlit
* 🐍 **Backend**: Python 3.10+
* 🧠 **LLM**: Mistral-7B-Instruct (GGUF quantized)
* 📦 **Libraries**: streamlit, llama-cpp-python, huggingface\_hub

---

## 🚀 Usage

1. **Place your model (.gguf file)** in the `models/` folder or set the environment variable:

   ```bash
   setx LLAMA_GGUF_PATH models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
   ```

2. **Run the generator:**

   ```bash
   python data_generator.py
   ```

3. **Explore conversations in the UI:**

   ```bash
   streamlit run app.py
   ```

---

## 📂 Key Files

* `data_generator.py` → Message and rationale generation
* `prompts/` → Prompt templates (message, rationale, paraphrase)
* `model_integration_local.py` → Local LLM wrapper
* `app.py` → Streamlit exploration UI

---

## 🎯 Future Roadmap

* 🌍 Multi-language conversations
* 📊 Analytics dashboard for clinicians
* 🧑‍🤝‍🧑 User profiles and personalization
* ⏱️ Real-time chat mode

---

## 📜 License

MIT License

---

🙌 *Built for Elyx Hackathon 2025 — combining AI, healthcare, and human touch.*

```

---

