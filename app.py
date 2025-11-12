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
# === HEADER WITH LOGO + TITLE ===
col1, col2 = st.columns([1, 4])
with col1:
    st.image("assets/logo.png", width=80)
with col2:
    st.markdown("""
    <h4 style="text-align:left;">
    ⭐ <strong>Artigellience Augmentation Aggregator (AAA)</strong> — Health Module ⭐
    </h4>
    <p><em>Powered by MindlyticsX | Curated by Sydney Singh</em></p>
    <p><strong>Understanding Health — Tailored for You.</strong></p>
    <hr style="margin: 0.8em 0; border: none; border-top: 1px solid #444;">
    <p style="font-size:14px; color:gray; text-align:left;">
    <em>Built with Vertex AI • Data Owned by You • Powered by AAA</em>
    </p>

    """, unsafe_allow_html=True)


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
import streamlit as st

# --- Footer & Vision Tagline ---
# === DISCLAIMER + FOOTER + TAGLINE ===
# === Optional Fade-in Animation & Glow Effect ===
# === DISCLAIMER + FOOTER + TAGLINE ===
st.markdown("""
<hr style="margin-top:2em; margin-bottom:1em; border: none; border-top: 1px solid #333;">

<div style="text-align: center; line-height: 1.6; animation: fadeIn 1.6s ease-in-out;">
  <p style="font-size:16px; font-weight:600;">
    ⭐ Artigellience Augmentation Aggregator (AAA) — Health Module ⭐
  </p>
  <p><em>Powered by MindlyticsX | Curated by Sydney Singh</em></p>
  <p style="font-weight:600;">Understanding Health — Tailored for You.</p>
  <p style="font-size:13px; color:#bbb; margin-top:0.5em; text-shadow: 0px 0px 6px rgba(0, 200, 255, 0.25);">
    🧠 The Orchestration Layer of Edge AI — As We Move from AI to AGI to ASI
  </p>
  <p style="margin-top:1em; font-size:13px; color:gray;">
    ⚕️ <b>Disclaimer:</b> This dashboard is for educational use only. No medical advice is provided.
  </p>
</div>

<style>
@keyframes fadeIn {
  from {opacity: 0; transform: translateY(10px);}
  to {opacity: 1; transform: translateY(0);}
}
</style>
""", unsafe_allow_html=True)




