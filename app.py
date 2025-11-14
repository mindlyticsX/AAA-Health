import os
import textwrap

import streamlit as st
import google.generativeai as genai


# ---------- 1. CONFIGURE PAGE ----------
st.set_page_config(
    page_title="AAA – Health Module",
    page_icon="🧠",
    layout="wide",
)

# ---------- 2. READ GEMINI KEY ----------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)

if not GEMINI_API_KEY:
    st.error(
        "GEMINI_API_KEY is missing in .streamlit/secrets.toml.\n\n"
        "Please add:\n\nGEMINI_API_KEY = \"your-key-here\""
    )
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini API directly (NOT Vertex / Model Garden)
MODEL_NAME = "gemini-1.5-flash"


# ---------- 3. HELPER: CALL GEMINI ----------
def run_aaa_health(prompt: str) -> str:
    """Send a health prompt to Gemini and return plain text."""
    system_instructions = textwrap.dedent(
        """
        You are AAA-Health, part of the Artigellence Augmentation Aggregator (AAA).

        Role:
        - Explain health topics clearly in simple language.
        - Focus on lifestyle, habits, prevention, and education.
        - Avoid diagnosing or prescribing specific treatment.
        - Always remind the user that this is not a substitute for a doctor.

        Style:
        - Friendly, calm, and supportive.
        - Short paragraphs and bullet points where helpful.
        - Highlight 3–5 key takeaways at the end under "AAA-Health Insight".
        """
    )

    full_prompt = f"{system_instructions}\n\nUser question:\n{prompt}"

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(full_prompt)
        # google-generativeai SDK usually exposes .text
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        # Fallback if needed
        parts = []
        for cand in response.candidates or []:
            for part in cand.content.parts:
                if getattr(part, "text", None):
                    parts.append(part.text)
        return "\n".join(parts).strip() or "No response text received from Gemini."
    except Exception as e:
        return f"⚠️ AAA-Health encountered an error while contacting Gemini:\n\n{e}"


# ---------- 4. UI LAYOUT ----------
col_logo, col_title = st.columns([1, 4])

with col_logo:
    st.image("assets/logo.png", width=80)

with col_title:
    st.markdown(
        """
        ### ⭐ Artigellence Augmentation Aggregator (AAA) — Health Module ⭐
        **Powered by MindlyticsX | Curated by Sydney Singh**

        _Understanding Health — Tailored for You._

        <small>Built with Gemini API • Data owned by you • Powered by AAA</small>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

st.subheader("▼ Enter a health prompt below")

default_prompt = "healthy sleep habits for adults"
user_prompt = st.text_input(
    "What do you want to explore?",
    value=default_prompt,
    placeholder="e.g., 'healthy sleep habits', 'low back pain after sitting', 'how to build a walking habit'",
)

run_btn = st.button("Run AAA Health AI", type="primary")

if run_btn:
    if not user_prompt.strip():
        st.warning("Please enter a health topic or question.")
    else:
        with st.spinner("AAA-Health is thinking..."):
            result = run_aaa_health(user_prompt)

        st.markdown("### 🧠 AAA-Health Insight")
        st.write(result)

st.markdown("---")
st.info(
    "This information is for educational purposes only and is **not** a substitute for "
    "professional medical advice, diagnosis, or treatment. Always consult a qualified "
    "healthcare professional for personal medical concerns."
)
