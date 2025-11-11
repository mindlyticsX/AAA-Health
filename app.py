import os
import streamlit as st

# -------------------------------------------------
# ✅ Load ENV Vars (set earlier in terminal)
# -------------------------------------------------
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")

# -------------------------------------------------
# ✅ Vertex init
# -------------------------------------------------
try:
    from vertexai import init as vertex_init
    from vertexai.generative_models import GenerativeModel
    HAVE_VERTEX = True
except ImportError:
    HAVE_VERTEX = False

# -------------------------------------------------
# ✅ Streamlit UI
# -------------------------------------------------
st.set_page_config(page_title="AAA Health", layout="wide")
st.title("Artigellence Augmentation Aggregator — Health Module")
st.subheader("MindlyticsX | Prototype Dashboard")

st.write("Welcome to the AAA Health prototype. This connects to **Google Vertex AI** for healthcare-style insights (demo only).")

query = st.text_input("Enter a symptom or topic:")

# -------------------------------------------------
# ✅ Function to call Vertex
# -------------------------------------------------
def ask_vertex(prompt):
    if not HAVE_VERTEX:
        return "❌ Vertex SDK missing. Run: pip install google-cloud-aiplatform vertexai"

    if not PROJECT_ID or not LOCATION:
        return "⚠️ PROJECT_ID / LOCATION missing. Restart terminal after exporting vars."

    try:
        vertex_init(project=PROJECT_ID, location=LOCATION)

        model = GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            [
                "You are a health information assistant. DO NOT give medical diagnosis.",
                "Summarize general information only and advise to consult professionals.",
                f"User question: {prompt}"
            ],
            generation_config={"max_output_tokens": 400}
        )

        return response.text or "⚠️ No response"
    except Exception as e:
        return f"❌ Vertex Error: {e}"

# -------------------------------------------------
# ✅ Run on submit
# -------------------------------------------------
if query:
    with st.spinner("Contacting Vertex AI..."):
        answer = ask_vertex(query)

    st.subheader("📎 Result")
    st.write(answer)

st.caption("⚠️ Educational demo only — not medical advice.")

