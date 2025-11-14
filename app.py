import streamlit as st
import google.generativeai as genai
from datetime import datetime

# =============================
# CONFIGURE GEMINI
# =============================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")


# =============================
# GEMINI TEST FUNCTION
# =============================
def gemini_test(question):
    try:
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        return f"Error: {e}"


# =============================
# AAA-HEALTH HOME UI SECTION
# =============================
def aaa_health_home():

    st.markdown("""
        <h1 style='text-align:center; color:#00C4CC; font-size:42px;'>
            AAA-Health Dashboard
        </h1>
        <p style='text-align:center; color:#808080; font-size:18px;'>
            Your personal health augmentation layer
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --- Main Module Grid ---
    st.subheader("Health Modules")
    col1, col2 = st.columns(2)

    with col1:
        st.button("🩺 Health Vault")
        st.button("📘 Health Log (Text/Voice)")
        st.button("🧪 Reports & Labs")

    with col2:
        st.button("📸 Visual Health Uploads")
        st.button("⚠️ Alerts & Reminders")
        st.button("🔐 Secure Sharing")

    st.markdown("---")

    # --- Quick Actions ---
    st.subheader("Quick Actions")
    st.button("🎤 Log Voice Note")
    st.button("📷 Upload a Photo")
    st.button("👨‍⚕️ Share with Doctor")

    st.markdown("---")

    # --- Footer ---
    st.markdown(
        f"<p style='text-align:center; color:#666;'>"
        f"AAA-Health v0.1 • Updated {datetime.now().strftime('%d %b %Y')}<br>"
        f"Your data. Your control. Always."
        f"</p>",
        unsafe_allow_html=True
    )


# =============================
# MAIN APP
# =============================
st.sidebar.title("AAA-Health Menu")

menu_choice = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "🧪 Gemini Test"
    ]
)

if menu_choice == "🏠 Home":
    aaa_health_home()

elif menu_choice == "🧪 Gemini Test":
    st.title("Gemini API Test (Working Baseline)")
    question = st.text_input("Enter your question:")
    
    if st.button("Ask Gemini"):
        if question.strip() == "":
            st.warning("Please enter a question.")
        else:
            st.write("**Response received!**")
            answer = gemini_test(question)
            st.write(answer)
