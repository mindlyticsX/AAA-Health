import streamlit as st
from PIL import Image
import os
from google.cloud import aiplatform

# === CONFIGURE PAGE ===
st.set_page_config(
    page_title="AAA Health Module",
    page_icon=Image.open("assets/favicon.ico"),
    layout="centered"
)

# === HEADER WITH LOGO + TITLE ===
col1, col2 = st.columns([1, 4])
with col1:
    st.image("assets/logo.png", width=80)
with col2:
    st.markdown("### ★ Artigellence Augmentation Aggregator — Health Module★")
    st.caption("Powered by MindlyticsX")

st.divider()

# === USER INPUT ===
st.subheader("▼ Enter a health prompt below")
user_input = st.text_area("What do you want to explore?", placeholder="e.g., side effects of aspirin")

# === VERTEX AI CALL ===
if st.button("Run AAA Health AI"):
    if user_input.strip():
        with st.spinner("Contacting Vertex AI..."):
            # Load env vars from Streamlit secrets
            project_id = st.secrets["PROJECT_ID"]
            location = st.secrets.get("LOCATION", "us-central1")
            endpoint = st.secrets["ENDPOINT_ID"]

            # Inject credentials for Vertex
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "backend/keys/aaa-health-key.json"

            # Initialize Vertex AI
            aiplatform.init(project=project_id, location=location)
            model = aiplatform.Predictor(endpoint=endpoint)

            # Request
            response = model.predict({
                "instances": [{"prompt": user_input}]
            })

            # Output
            st.success("✅ AI Response:")
            st.write(response)
    else:
        st.warning("⚠️ Please enter a health prompt first.")




# === CTA BUTTONS ===
st.markdown("### 🌐 Explore More")
col1, col2, col3 = st.columns(3)
with col1:
    st.link_button("🏠 Website", "https://www.mindlytics.xyz")
with col2:
    st.link_button("🎧 Podcast", "https://open.spotify.com/")
with col3:
    st.link_button("💬 Community", "https://chat.whatsapp.com/IsaVnhlyiMLD7mQuAZ3s5m")

# === DISCLAIMER FOOTER ===
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 14px; color: gray;'>
        © 2025 MindlyticsX · All rights reserved.<br>
        <b>Disclaimer:</b> This dashboard is for educational use only. No medical advice is provided.
    </div>
    """,
    unsafe_allow_html=True
)
