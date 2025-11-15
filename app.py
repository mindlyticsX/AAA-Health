import streamlit as st
import google.generativeai as genai

# -----------------------------------------
# Gemini API KEY Debug Check
# -----------------------------------------
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ GEMINI_API_KEY not found in Streamlit secrets.\n\nGo to App Settings → Secrets → Add:\nGEMINI_API_KEY = \"YOUR_KEY_HERE\"")
    st.stop()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# -----------------------------------------
# Streamlit UI
# -----------------------------------------
st.title("💎 AAA - Health | Gemini Test")
st.write("This is a simple test to confirm Gemini API + Streamlit are working.")

prompt = st.text_input("Enter your question:")

if prompt:
    try:
        with st.spinner("Thinking..."):
            response = model.generate_content(prompt)

        st.success("Response received!")
        st.write(response.text)

    except Exception as e:
        st.error("⚠️ Error communicating with Gemini API.")
        st.code(str(e))
