import streamlit as st
import google.generativeai as genai

# -------------------------------------------------
# 1. CONFIGURE PAGE
# -------------------------------------------------
st.set_page_config(
    page_title="AAA - Health | Gemini Test",
    page_icon="💎",
    layout="centered",
)

# -------------------------------------------------
# 2. LOAD GEMINI API KEY FROM SECRETS
# -------------------------------------------------
# Streamlit `.streamlit/secrets.toml` structure:
# GEMINI_API_KEY = "YOUR_KEY_HERE"
# [general]
# project_id = "projects/570044963459"
# location   = "us-central1"

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ GEMINI_API_KEY not found in Streamlit secrets.")
    st.stop()

genai.configure(api_key=api_key)

# Use a fast, stable Gemini model name here
MODEL_NAME = "gemini-2.0-flash"


def get_gemini_model():
    """Return a configured Gemini model."""
    return genai.GenerativeModel(MODEL_NAME)


# -------------------------------------------------
# 3. SIMPLE AAA-HEALTH LAYOUT SHELL
# -------------------------------------------------
st.title("💎 AAA - Health | Gemini Test")

st.write(
    """
This is your **baseline AAA-Health checker** to confirm Gemini API + Streamlit are working correctly.

Over time, this page will grow into the full AAA-Health module:

- 🗄️ **Health Vault** – store & organise your health notes and documents  
- 📝 **Health Log** – daily/weekly logs (sleep, food, mood, symptoms)  
- 📊 **Insights** – gentle, AI-assisted explanations & patterns  

For now, we are only **testing questions** with Gemini to keep things simple and stable.
"""
)

st.write("---")

st.info(
    "⚠️ This tool is for **information and education only**. "
    "It does **not** replace professional medical advice, diagnosis, or treatment."
)

st.write("---")

# -------------------------------------------------
# 4. MAIN QUESTION → GEMINI ANSWER
# -------------------------------------------------
st.subheader("Ask a health-related question")

prompt = st.text_input("Enter your question:")

if prompt:
    model = get_gemini_model()

    try:
        with st.spinner("Thinking..."):
            response = model.generate_content(prompt)

        st.success("Response received!")
        # response.text works for normal text outputs
        st.write(response.text)

    except Exception as e:
        st.error("⚠️ Error communicating with Gemini API.")
        st.code(str(e))
