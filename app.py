import streamlit as st
import json
import google.generativeai as genai
from PIL import Image

# ---------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------
st.set_page_config(
    page_title="AAA Health Module",
    page_icon="✨",
    layout="centered"
)

# ---------------------------------------------
# HEADER SECTION WITH LOGO + TITLE
# ---------------------------------------------
col1, col2 = st.columns([1, 4])

with col1:
    st.image("assets/logo.png", width=120)

with col2:
    st.markdown("""
        <div style="text-align:left;">
            <h2>⭐ Artigellience Augmentation Aggregator (AAA) — Health Module ⭐</h2>
            <p><i>Powered by MindlyticsX | Curated by Sydney Singh</i></p>
            <p><strong>Understanding Health — Tailored for You.</strong></p>
            <p><small>Built with Gemini — Data Owned by You — Powered by AAA</small></p>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# ---------------------------------------------
# LOAD GOOGLE SERVICE ACCOUNT FROM SECRETS
# ---------------------------------------------
service_account_info = json.loads(st.secrets["google_credentials"])

genai.configure(credentials=service_account_info)

model = genai.GenerativeModel("gemini-2.0-flash")

# ---------------------------------------------
# INPUT BOX
# ---------------------------------------------
st.subheader("▼ Enter a health prompt below")

user_input = st.text_area(
    "What do you want to explore?",
    placeholder="Example: Foods that improve sleep quality",
    height=120
)

# ---------------------------------------------
# RUN AAA HEALTH AI
# ---------------------------------------------
if st.button("Run AAA Health AI"):
    if user_input.strip():
        with st.spinner("Contacting Gemini…"):
            try:
                response = model.generate_content(user_input)
                st.success("Response received:")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ---------------------------------------------
# QUICK LINKS
# ---------------------------------------------
st.write("---")
st.subheader("🌐 Explore More")

colA, colB, colC = st.columns(3)

with colA:
    st.link_button("🔒 Website", "https://mindlytics.xyz")

with colB:
    st.link_button("🎙️ Podcast", "https://google.com")

with colC:
    st.link_button("💬 Community", "https://chat.whatsapp.com/IsaVnhlyiMLD7mQuAZ3s5m")

st.write("---")

st.markdown("""
<div style="text-align:center;">
    <small>⚙️ The Orchestration Layer of Edge AI — As We Move from AI to AGI to ASI</small><br>
    <small>⚠ Disclaimer: This dashboard is for educational use only. No medical advice is provided.</small>
</div>
""", unsafe_allow_html=True)
