import streamlit as st
import google.generativeai as genai
from datetime import datetime

# ---------------------------------------------------------
# 1. PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="AAA - Health | Gemini Test",
    page_icon="💎",
    layout="centered",
)

# ---------------------------------------------------------
# 2. LOAD GEMINI API KEY FROM SECRETS
# ---------------------------------------------------------
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("❌ Could not load Gemini API key from secrets.")
    st.code(str(e))
    st.stop()


# ---------------------------------------------------------
# 3. HELPER: GET GEMINI MODEL
# ---------------------------------------------------------
def get_gemini_model():
    # This is the model that is already working for you
    return genai.GenerativeModel("gemini-2.0-flash")


# ---------------------------------------------------------
# 4. INITIALISE SESSION STATE
# ---------------------------------------------------------
if "health_log" not in st.session_state:
    st.session_state["health_log"] = []  # list of dicts

if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []  # list of dicts

if "last_question" not in st.session_state:
    st.session_state["last_question"] = ""

if "last_answer" not in st.session_state:
    st.session_state["last_answer"] = ""


# ---------------------------------------------------------
# 5. PAGE HEADER + DISCLAIMER
# ---------------------------------------------------------
st.title("💎 AAA - Health | Gemini Test")

st.write(
    "This is your baseline AAA-Health checker to confirm Gemini API + Streamlit are working correctly.\n\n"
    "Over time, this page will grow into the full AAA-Health module:"
)

st.markdown(
    """
- 📁 **Health Vault** – store & organise your health notes and documents  
- 📘 **Health Log** – daily/weekly logs (sleep, food, mood, symptoms)  
- 🔍 **Insights** – gentle, AI-assisted explanations & patterns  

For now, we are only testing questions to keep things simple and stable.
"""
)

st.warning(
    "⚠️ This tool is for information and education only. "
    "It does not replace professional medical advice, diagnosis, or treatment."
)

st.markdown("---")

# ---------------------------------------------------------
# 6. MAIN TABS
# ---------------------------------------------------------
tab_ask, tab_log, tab_vault = st.tabs(
    ["🧠 Ask AI", "📝 Health Log", "📂 Health Vault (Coming Soon)"]
)

# ---------------------------------------------------------
# TAB 1 – ASK AI
# ---------------------------------------------------------
with tab_ask:
    st.subheader("Ask a health-related question")

    question = st.text_input("Enter your question:")

    ask_button = st.button("Ask Gemini", type="primary")

    if ask_button and question.strip():
        model = get_gemini_model()

        try:
            with st.spinner("Thinking..."):
                response = model.generate_content(question)
                answer = response.text

            st.success("Response received!")
            st.write(answer)

            # Save last Q&A in session state
            st.session_state["last_question"] = question
            st.session_state["last_answer"] = answer

            # Also keep a simple Q&A history (in memory for now)
            st.session_state["qa_history"].append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "question": question,
                    "answer": answer,
                }
            )

        except Exception as e:
            st.error("⚠️ Error communicating with Gemini API.")
            st.code(str(e))

    # Optional: Save last answer into Health Log
    if st.session_state.get("last_answer"):
        if st.button("Save this answer to Health Log"):
            st.session_state["health_log"].append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "source": "AI",
                    "title": st.session_state.get("last_question", "AI guidance"),
                    "text": st.session_state["last_answer"],
                }
            )
            st.success("Saved to Health Log. You can view it in the 'Health Log' tab.")


# ---------------------------------------------------------
# TAB 2 – HEALTH LOG (text-only v0.1)
# ---------------------------------------------------------
with tab_log:
    st.subheader("Quick daily note")

    note = st.text_area(
        "How are you feeling today? (symptoms, mood, sleep, food, etc.)",
        height=120,
    )

    if st.button("Save note to Health Log"):
        if note.strip():
            st.session_state["health_log"].append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "source": "You",
                    "title": "Daily note",
                    "text": note.strip(),
                }
            )
            st.success("Note saved to Health Log.")
        else:
            st.info("Please type something before saving.")

    st.markdown("---")
    st.markdown("### Your Health Log entries")

    if st.session_state["health_log"]:
        # Show newest first
        for entry in reversed(st.session_state["health_log"]):
            st.markdown(f"**{entry['timestamp']} – {entry['title']} ({entry['source']})**")
            st.write(entry["text"])
            st.markdown("---")
    else:
        st.info(
            "No entries yet. Use the form above or the 'Save this answer to Health Log' "
            "button in the Ask AI tab to start building your log."
        )


# ---------------------------------------------------------
# TAB 3 – HEALTH VAULT (COMING SOON)
# ---------------------------------------------------------
with tab_vault:
    st.subheader("Health Vault (Coming Soon)")
    st.info(
        "This section will let you upload and organise reports, prescriptions, and "
        "other health documents. For now, it's just a placeholder while we keep the "
        "Gemini connection stable."
    )
