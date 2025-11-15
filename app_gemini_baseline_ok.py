import streamlit as st
import google.generativeai as genai

# -------------------------------------------------
# 1. PAGE SETUP
# -------------------------------------------------
st.set_page_config(
    page_title="AAA - Health | Gemini Test",
    page_icon="💎",
    layout="centered",
)

st.title("💎 AAA - Health | Gemini Test")
st.write("This is a simple test to confirm Gemini API + Streamlit are working correctly.")

# -------------------------------------------------
# 2. LOAD GEMINI API KEY FROM SECRETS
# -------------------------------------------------

# st.secrets structure:
# [general]
#   project_id = "..."
#   location = "..."
#   google_credentials = """..."""
#   GEMINI_API_KEY = "YOUR_KEY"
#
# So the key is inside the "general" section.

general_secrets = st.secrets.get("general", {})

if "GEMINI_API_KEY" not in general_secrets:
    st.error(
        "❌ GEMINI_API_KEY not found in Streamlit secrets.\n\n"
        "Go to App Settings → Secrets and make sure it is defined "
        "inside the [general] section as:\n\n"
        'GEMINI_API_KEY = "YOUR_KEY_HERE"'
    )
    st.stop()

api_key = general_secrets["GEMINI_API_KEY"]

# -------------------------------------------------
# 3. CONFIGURE GEMINI
# -------------------------------------------------
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
except Exception as e:
    st.error("⚠️ Error configuring Gemini. Please check API key and project settings.")
    st.code(str(e))
    st.stop()

# -------------------------------------------------
# 4. SIMPLE CHAT UI
# -------------------------------------------------
prompt = st.text_input("Enter your question:")

if prompt:
    try:
        with st.spinner("Thinking..."):
            response = model.generate_content(prompt)

        st.success("Response received!")
        # response.text works for normal text outputs
        st.write(response.text)

    except Exception as e:
        st.error("⚠️ Error communicating with Gemini API.")
        st.code(str(e))
