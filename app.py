import streamlit as st
import google.generativeai as genai

# -----------------------------------------------------------
# 1. PAGE CONFIG
# -----------------------------------------------------------
st.set_page_config(
    page_title="AAA – Health | Gemini Test",
    page_icon="💎",
    layout="centered",
)

# -----------------------------------------------------------
# 2. LOAD GEMINI API KEY FROM SECRETS
# -----------------------------------------------------------
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("❌ Could not load Gemini API key from secrets.")
    st.code(str(e))
    st.stop()

# -----------------------------------------------------------
# 3. SHOW HEADER
# -----------------------------------------------------------
st.title("💎 AAA - Health | Gemini Test")
st.write("""
This is your baseline AAA-Health checker to confirm Gemini API + Streamlit are working correctly.

Over time, this page will grow into the full AAA-Health module:

- 🗂 **Health Vault** – store & organise your health notes and documents  
- 📘 **Health Log** – daily/weekly logs (sleep, food, mood, symptoms)  
- 🔍 **Insights** – gentle, AI-assisted explanations & patterns  

For now, we are only testing questions to keep things simple and stable.
""")

# -----------------------------------------------------------
# 4. DISCLAIMER
# -----------------------------------------------------------
st.warning("""
⚠️ **This tool is for information and education only.  
It does not replace professional medical advice, diagnosis, or treatment.**
""")

st.write("---")

# -----------------------------------------------------------
# 5. ASK THE QUESTION
# -----------------------------------------------------------
st.subheader("Ask a health-related question")

prompt = st.text_input("Enter your question:")

# -----------------------------------------------------------
# 6. GEMINI MODEL LOADER
# -----------------------------------------------------------
def get_gemini_model():
    return genai.GenerativeModel("gemini-2.0-flash")

# -----------------------------------------------------------
# 7. PROCESS THE QUESTION
# -----------------------------------------------------------
if prompt:
    try:
        model = get_gemini_model()

        with st.spinner("Thinking..."):
            response = model.generate_content(prompt)

        st.success("Response received!")
        st.write(response.text)  # writes formatted text

    except Exception as e:
        st.error("⚠️ Error communicating with Gemini API.")
        st.code(str(e))

st.write("---")

# -----------------------------------------------------------
# END OF FILE
# -----------------------------------------------------------
