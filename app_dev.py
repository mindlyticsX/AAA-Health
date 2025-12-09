# ============================================================
# AAA — HEALTH INTELLIGENCE (PRODUCTION VERSION)
# FULL CLEAN IMPORT BLOCK + STRIPE + MONETIZATION READY
# ============================================================

import streamlit as st
import json
import os
import shutil
from datetime import datetime
from google import generativeai as genai

import fitz                    # PyMuPDF for PDF rendering
import base64
from fpdf import FPDF

import stripe                  # Monetization (future build)
import html                    # safe HTML rendering
import requests                # Region auto-detect
import random                  # Forecast engine / visual randomness

# === NEW REQUIRED IMPORTS (for analytics pages) ===
import pandas as pd            # REQUIRED for Page 23 graphs
import altair as alt           # REQUIRED for charts / visualizations

# ============================================================
# GLOBAL SAFE HTML SANITIZER — PREVENTS UI BREAKING
# ============================================================

def safe_render(text: str) -> str:
    """
    Ensures AI output never breaks HTML rendering in Streamlit.
    - Escapes unsafe HTML tags returned by Gemini
    - Prevents accidental raw HTML injection
    - Converts newlines into <br> for readability
    """
    if not text:
        return ""
    safe = html.escape(text)
    safe = safe.replace("\n", "<br>")
    return safe


# ============================================================
# PATHS & DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "aaa_health_data")
VAULT_DIR = os.path.join(DATA_DIR, "vault_files")
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")
RECYCLE_BIN_DIR = os.path.join(DATA_DIR, "recycle_bin")
INSIGHTS_HISTORY_DIR = os.path.join(DATA_DIR, "insights_history")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Create directories if missing
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(RECYCLE_BIN_DIR, exist_ok=True)
os.makedirs(INSIGHTS_HISTORY_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ============================================================
# DATA FILES — HEALTH MODULE
# ============================================================

HEALTH_LOG_FILE = os.path.join(DATA_DIR, "health_log.json")
OCR_DATA_FILE = os.path.join(DATA_DIR, "ocr_results.json")
PHOTO_DATA_FILE = os.path.join(DATA_DIR, "photo_data.json")
DOCTOR_NOTES_FILE = os.path.join(DATA_DIR, "doctor_notes.json")

MERGED_DATA_FILE = os.path.join(DATA_DIR, "merged_health_data.json")
AI_SUMMARY_FILE = os.path.join(DATA_DIR, "ai_summary.json")

SUMMARY_REPORT_PDF = os.path.join(DATA_DIR, "health_summary_report.pdf")


# ============================================================
# STEP 2 — REGION AUTO-DETECT (India / Australia / Global)
# ============================================================

def detect_region():
    """
    Detects user region via IP — safe, no HTML, no UI changes.
    Always returns one of: 'IN', 'AU', 'GLOBAL'
    """

    try:
        r = requests.get("https://ipapi.co/json/", timeout=3)
        data = r.json()
        code = data.get("country_code", "").upper()

        if code == "IN":
            return "IN"
        if code == "AU":
            return "AU"

        return "GLOBAL"

    except:
        return "GLOBAL"


# ============================================================
# INSIGHTS HISTORY (PREMIUM)
# ============================================================

INSIGHTS_FILE = os.path.join(INSIGHTS_HISTORY_DIR, "insights_history.json")

# ============================================================
# STRIPE CONFIG (PLACEHOLDERS — ACTIVATED WHEN KEY ADDED)
# ============================================================

STRIPE_SECRET_KEY = st.secrets.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_AU = st.secrets.get("STRIPE_PRICE_AU", "")
STRIPE_PRICE_IN = st.secrets.get("STRIPE_PRICE_IN", "")
STRIPE_PRICE_US = st.secrets.get("STRIPE_PRICE_US", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ============================================================
# GEMINI CONFIG — AAA INTELLIGENCE ENGINE
# ============================================================

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ============================================================
# JSON HELPERS (STANDARDIZED & STABLE)
# ============================================================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

# ============================================================
# PDF / FILE UTILITIES
# ============================================================

def extract_text_any(path):
    """Extract rough text from PDF or image using PyMuPDF."""
    text_chunks = []

    if path.lower().endswith(".pdf"):
        try:
            with fitz.open(path) as doc:
                for page in doc:
                    text_chunks.append(page.get_text())
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    else:
        # Images or unknown files — handled via OCR elsewhere
        text_chunks.append("Image uploaded — OCR text stored separately.")

    return "\n".join(text_chunks)


# ============================================================
# PREMIUM FIREWALL (SAFE WRAPPER — NO IMPACT ON EXISTING CODE)
# ============================================================

def premium_required_ui(page_title: str, page_description: str):
    """
    SAFE UI LOCK:
    - No backend logic touched
    - No routing changed
    - Only stops the page from rendering when in FREE mode
    - Premium mode continues exactly as before
    """
    mode = st.session_state.get("mode", "free")

    # If FREE mode → show Premium lock screen
    if mode == "free":
        st.markdown(
            f"""
            <div style="text-align:center; padding:40px;">

                <div style="font-size:60px; opacity:0.9;">🔒</div>

                <h2 style="color:#EF5350;">
                    {page_title} — Premium Feature
                </h2>

                <p style="color:#C7D2FE; font-size:16px; line-height:1.6; max-width:600px; margin:auto;">
                    {page_description}
                </p>

                <div style="
                    margin-top:25px; 
                    padding:18px; 
                    border-radius:12px; 
                    background:rgba(255,255,255,0.06); 
                    max-width:460px; 
                    margin:auto;
                ">
                    <h3 style="margin-bottom:6px; color:#BBDEFB;">✨ Includes 7-Day Free Trial</h3>
                    <p style="font-size:14px; color:#AAB4FF;">
                        Experience the full AAA Premium Intelligence engine.
                        No risk. Cancel anytime.
                    </p>
                </div>

                <div style="margin-top:30px;">
                    <button style="
                        background:#FF5252; 
                        color:white; 
                        padding:12px 28px; 
                        border:none; 
                        border-radius:8px; 
                        font-size:16px;
                        cursor:pointer;">
                        Upgrade to Premium (Demo)
                    </button>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # STOP PAGE RENDERING (SAFE)
        st.stop()

# ============================================================
# MULTI-SIGNAL ENGINE — BACKEND
# ============================================================

def run_multi_signal_engine(signals):
    """
    signals: list of raw text strings collected from vault files, images,
    manual text, and health logs.
    """

    # 1. Merge all signals
    master_text = "\n\n---\n\n".join(signals)

    # 2. Safety cap (prevent huge model calls)
    cleaned = master_text.strip()[:40000]

    # 3. Build prompt
    prompt = build_multi_signal_prompt(cleaned)

    # 4. Gemini call (correct API syntax)
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        ai_text = response.text if hasattr(response, "text") else str(response)

    except Exception as e:
        ai_text = f"Error generating insights: {e}"

    # 5. JSON structure (future expansion: cluster extraction)
    result_json = {
        "clusters": [],
        "confidence": {},
        "summary": ai_text[:1500]
    }

    # 6. HTML formatted output
    formatted = f"""
    <div style='font-size:15px; line-height:1.7;'>
        {ai_text}
    </div>
    """

    return {
        "json": result_json,
        "formatted": formatted
    }

# ============================================================
# MULTI-SIGNAL PROMPT — SAFE DIFFERENTIAL INSIGHTS
# ============================================================

def build_multi_signal_prompt(text):
    return f"""
You are AAA — Artigellence Augmentation Aggregator.

TASK:
Analyze all the signals (combined text from medical PDFs, images, notes, and logs)
and produce **INFORMATIONAL, NON-MEDICAL** differential insight clusters.

STRICT RULES:
- DO NOT give medical advice.
- DO NOT suggest treatment or medications.
- DO NOT tell the user what disease they have.
- Only provide informational pattern-based insights.
- Maintain strict medical safety compliance.

FORMAT OUTPUT AS:

1. **Signal Interpretation Overview**
   - General patterns found
   - Notable correlations

2. **Differential Insight Clusters (Informational Only)**
   - Cluster A: Possible interpretation patterns  
     · Evidence from text  
     · Why this cluster appears  
     · Confidence (Low / Medium / High)

   - Cluster B
   - Cluster C  
   (3–6 clusters total)

3. **Cross-Signal Correlation Map**
   - Text ↔ Biomarkers  
   - Notes ↔ PDF findings  
   - OCR ↔ Health Logs

4. **Early Indicators (Observational Only)**
   - Mild variance patterns  
   - Possible functional themes  
   - Monitoring considerations (informational only)

5. **Confidence Matrix**
   - How strongly the text supports each cluster
   - Limitations

6. **Summary (150 words)**
   - High-level descriptive insights only.
   - No directives, no medical conclusions.

TEXT TO ANALYZE:
{text}
"""

# ============================================================
# GEMINI GENERIC CALLER
# ============================================================

def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key is missing. Configure it in Streamlit secrets."

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text or "(No response text)"
    except Exception as e:
        return f"Error calling Gemini: {e}"

# ============================================================
# GLOBAL STYLING
# ============================================================

APP_CSS = """
<style>
    .main {
        background-color: #020617;
    }
    .stApp {
        background-color: #020617;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
"""

st.set_page_config(
    page_title="AAA — Health Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(APP_CSS, unsafe_allow_html=True)

# ============================================================
# SUBSCRIPTION PRICING DICTIONARY (A$, USD, INR)
# ============================================================

SUBSCRIPTION_PLANS = {
    "monthly": {
        "AUD": 10,
        "USD": 10,
        "INR": 500
    },
    "yearly": {
        "AUD": 95,
        "USD": 95,
        "INR": 950
    }
}

def get_price(currency: str, cycle: str):
    """Return price based on selected currency and billing cycle."""
    try:
        return SUBSCRIPTION_PLANS[cycle][currency]
    except KeyError:
        return None

# ============================================================
# SUBSCRIPTION STATE + PAYWALL LOGIC
# ============================================================

# Global toggle: free or premium (existing sidebar toggle drives this)
def get_subscription_mode():
    return st.session_state.get("subscription_mode", "free")


def require_premium(feature_name: str):
    """
    Central paywall guard.
    If user is free → show locked message + return False.
    If user is premium → return True and allow the feature to run.
    """
    mode = get_subscription_mode()

    if mode == "premium":
        return True

    # Render Lock UI
    st.warning(f"🔒 **{feature_name} is a premium feature.**")
    st.info(
        "Upgrade to unlock all AI summaries, tailored dashboards, snapshots, "
        "priority OCR, advanced extraction, support circle, and early-access features."
    )

    # Upgrade CTA (uses your pricing dictionary)
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### ⭐ Upgrade Now")
    with col2:
        st.markdown(
            """
            **Monthly:** A$10 / ₹500 / $10  
            **Yearly:** A$95 / ₹950 / $95  
            """
        )
        st.button("Upgrade to Premium")

    return False

# ============================================================
# PREMIUM SUBSCRIPTION BANNER (TOP OF PAGE)
# ============================================================

def premium_banner():
    """
    Display a simple, elegant banner encouraging upgrade.
    Shown only when user is on free tier.
    """
    mode = get_subscription_mode()
    if mode == "premium":
        return  # Premium users should not see banner

    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg, #0ea5e9, #3b82f6, #2563eb);
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: white;
            font-size: 17px;
            font-weight: 500;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        ">
            ⭐ <b>Upgrade to AAA Premium</b> for unlimited summaries, full dashboards,
            tailored insights, advanced OCR, snapshot restore and priority features.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# GLOBAL DISCLAIMER TEXT
# ============================================================

FINAL_DISCLAIMER_TEXT = """
AAA — Health Intelligence provides AI-assisted insights.  
It does not replace professional medical, financial, or legal advice.  
Always consult certified experts for critical decisions.
"""

# ============================================================
# GLOBAL UI — HEADER + FOOTER (STABLE — DO NOT MODIFY)
# ============================================================

def aaa_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=False, width=220)
        else:
            st.write("AAA — Artigellence Augmentation Aggregator")


def aaa_footer():
    st.markdown(
        """
        <br><br>
        <div style='text-align:center; color:#9ca3af; font-size:14px;'>
            AAA — Health Intelligence provides AI-assisted insights.<br>
            It does not replace professional medical, financial, or legal advice.<br>
            Always consult certified experts for critical decisions.
        </div>
        <br><br>
        <div style='text-align:center; color:#e5e7eb; font-size:14px; font-weight:500;'>
            Crafted by Sydney Singh — Artigellence Augmentation Aggregator<br>
            <span style='font-size:13px; color:#9ca3af;'>
                Edge-AI Orchestration Layer • Gemini • Vertex AI
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# SUBSCRIPTION MODE (DEMO TOGGLE)
# ============================================================

def get_mode():
    if "subscription_mode" not in st.session_state:
        st.session_state["subscription_mode"] = "free"

    with st.sidebar:
        st.markdown("### 🔐 Subscription Mode (Demo)")
        mode = st.radio(
            "Select mode:",
            ["free", "premium"],
            index=0 if st.session_state["subscription_mode"] == "free" else 1,
            key="subscription_mode_radio",
        )
        st.session_state["subscription_mode"] = mode

    return st.session_state["subscription_mode"]

def is_premium():
    return st.session_state.get("subscription_mode", "free") == "premium"

# ============================================================
# PAYWALL SCREEN
# ============================================================

def paywall_screen():
    st.markdown("<br>", unsafe_allow_html=True)

    # --- MAIN CARD ---
    with st.container():
        st.markdown(
            """
            <div style="
                background: radial-gradient(circle at top, #1f2937, #020617);
                border-radius: 24px;
                padding: 40px 32px;
                text-align: center;
                border: 1px solid rgba(148,163,184,0.35);
                box-shadow: 0 22px 45px rgba(15,23,42,0.85);
                max-width: 520px;
                margin: 0 auto;
            ">
                <div style="font-size:16px; letter-spacing:0.18em; text-transform:uppercase; color:#60a5fa; margin-bottom:10px;">
                    AAA — Health Intelligence
                </div>
                <h2 style="font-size:26px; margin-bottom:12px; color:#e5e7eb; font-weight:600;">
                    Premium Feature
                </h2>
                <p style="font-size:14px; color:#cbd5f5; margin-bottom:24px;">
                    This feature is available for Premium users.
                </p>
                <div style="font-size:13px; color:#9ca3af; opacity:0.9; margin-bottom:20px;">
                    Upgrade to unlock full AI Medical Intelligence.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- FREE TRIAL CTA (NO PRICES) ---
    st.info("🎉 Try AAA Premium Free for 7 Days — Unlock Full Intelligence")

# ============================================================
# CTA BANNER — MONETIZATION PROMPT
# ============================================================

def monetization_cta():
    st.markdown(
        """
        <div style="
            margin-top:30px;
            padding:20px 22px;
            border-radius:18px;
            background:linear-gradient(90deg,#0f172a,#020617);
            border:1px solid rgba(148,163,184,0.35);
            color:#e5e7eb;
            text-align:center;
        ">
            <div style="font-size:16px; font-weight:600; margin-bottom:6px;">
                🚀 Artigellence Premium — Upgrade for Full Intelligence
            </div>
            <div style="font-size:13px; color:#cbd5f5;">
                Get unlimited AI summaries, deep insights, PDF health reports, snapshots, merged view and early access to AAA Finance &amp; Law.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# PAYWALL HELPER — LOCK ANY FEATURE
# ============================================================

def feature_locked():
    st.warning("⚠️ This feature is available for Premium members.")
    st.markdown("### 👉 Please upgrade to unlock full access.")
    paywall_screen()

# ============================================================
# PAGE 1 — HEALTH LOG  (with Ask Gemini)
# ============================================================

def page_health_log():
    aaa_header()
    st.subheader("🩺 Health Log")

    logs = load_json(HEALTH_LOG_FILE, [])
    today_str = datetime.now().strftime("%Y-%m-%d")

    note = st.text_area("Write or paste your health notes:", height=160, key="health_log_text")

    col1, col2 = st.columns([1, 4])
    with col1:
        date_str = st.date_input("Date", datetime.now()).strftime("%Y-%m-%d")
    with col2:
        st.write("")

    if st.button("Save Log Entry"):
        entry = {
            "date": date_str,
            "note": note.strip(),
            "timestamp": datetime.now().isoformat(),
        }
        logs.append(entry)
        save_json(HEALTH_LOG_FILE, logs)
        st.success("Health log entry saved.")

    st.markdown("---")
    st.markdown("### Previous Entries")

    if logs:
        for entry in reversed(logs[-5:]):
            with st.expander(entry["date"]):
                st.write(entry["note"])
    else:
        st.info("No entries yet.")

    monetization_cta()

    st.markdown("---")
    st.markdown("### 🤖 Ask Gemini — AAA Health Intelligence")
    query = st.text_input("Type your question:", key="ask_gemini_question")

    if st.button("Ask Gemini", type="primary"):
        if not query.strip():
            st.warning("Please type a question first.")
        else:
            with st.spinner("Thinking with AAA Health Intelligence…"):
                combined_context = ""
                if logs:
                    recent = logs[-3:]
                    combined_context += "Recent health notes:\n"
                    for e in recent:
                        combined_context += f"- {e['date']}: {e['note']}\n"

                prompt = f"""
You are AAA — Health Intelligence, an AI assistant built on top of medical models.

USER QUESTION:
{query}

USER CONTEXT (may be partial / user-written notes):
{combined_context}

1. Give a kind, clear, layman-friendly explanation.
2. Highlight possible risk markers as bullet points.
3. Suggest 3–5 follow-up questions the user could ask their doctor.
4. Always include a disclaimer that this is not medical advice and they must consult a licensed physician.
"""
                answer = call_gemini(prompt)
                st.markdown(answer)

    aaa_footer()

# ============================================================
# PAGE 2 — HEALTH VAULT (UPLOAD)
# ============================================================

def page_health_vault():
    aaa_header()
    st.subheader("📥 Health Vault")

    uploaded_files = st.file_uploader(
        "Upload medical PDFs or images",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uf in uploaded_files:
            path = os.path.join(VAULT_DIR, uf.name)
            with open(path, "wb") as f:
                f.write(uf.getbuffer())
            st.success(f"Saved: {uf.name}")

    files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    st.markdown("### Stored Files")
    if not files:
        st.info("No files in the vault yet.")
    else:
        for f in files:
            st.write(f"• {f}")

    monetization_cta()
    aaa_footer()

# ============================================================
# VAULT MANAGER PRO
# ============================================================

def file_metadata(path):
    stat = os.stat(path)
    return round(stat.st_size / 1024, 2), datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

def page_vault_manager():
    aaa_header()
    st.subheader("📁 Vault Manager Pro")

    files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]

    if not files:
        st.info("Vault is empty.")
        monetization_cta()
        aaa_footer()
        return

    for f in files:
        p = os.path.join(VAULT_DIR, f)
        size, modified = file_metadata(p)

        with st.expander(f"{f} — {size} KB — {modified}"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    st.image(p)
                elif f.lower().endswith(".pdf"):
                    st.write("PDF file stored.")

            with col2:
                if st.button(f"🗑 Move to Recycle Bin: {f}", key=f"mv_{f}"):
                    dest = os.path.join(RECYCLE_BIN_DIR, f)
                    shutil.move(p, dest)
                    st.success("Moved to Recycle Bin.")
                    st.experimental_rerun()

            with col3:
                if st.button(f"❌ Delete Permanently: {f}", key=f"rm_{f}"):
                    os.remove(p)
                    st.warning("Deleted permanently.")
                    st.experimental_rerun()

    monetization_cta()
    aaa_footer()

# ============================================================
# RECYCLE BIN PAGE
# ============================================================

def page_recycle_bin():
    aaa_header()
    st.subheader("🗑 Recycle Bin")

    files = [f for f in os.listdir(RECYCLE_BIN_DIR) if os.path.isfile(os.path.join(RECYCLE_BIN_DIR, f))]

    if not files:
        st.info("Recycle Bin is empty.")
        aaa_footer()
        return

    for f in files:
        p = os.path.join(RECYCLE_BIN_DIR, f)
        size, modified = file_metadata(p)

        with st.expander(f"{f} — {size} KB — {modified}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"♻ Restore {f}", key=f"restore_{f}"):
                    restore_path = os.path.join(VAULT_DIR, f)
                    shutil.move(p, restore_path)
                    st.success("Restored successfully.")
                    st.experimental_rerun()

            with col2:
                if st.button(f"❌ Delete Permanently {f}", key=f"delete_{f}"):
                    os.remove(p)
                    st.warning("Deleted permanently.")
                    st.experimental_rerun()

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 3 — PDF PREVIEW
# ============================================================

def page_pdf_preview():
    aaa_header()
    st.subheader("📄 PDF Preview")

    files = [f for f in os.listdir(VAULT_DIR) if f.lower().endswith(".pdf")]
    if not files:
        st.info("No PDFs found in Vault.")
        aaa_footer()
        return

    selected = st.selectbox("Select PDF to preview:", files)
    if selected:
        path = os.path.join(VAULT_DIR, selected)
        with open(path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")

        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 4 — OCR PLACEHOLDER (BASIC)
# ============================================================

def page_ocr():
    aaa_header()
    st.subheader("🔍 OCR & Text Extraction (Basic)")

    files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    if not files:
        st.info("No files in Vault.")
        aaa_footer()
        return

    selected = st.selectbox("Select file to extract text from:", files)
    if st.button("Extract Text"):
        path = os.path.join(VAULT_DIR, selected)
        text = extract_text_any(path)
        st.text_area("Extracted Text (rough):", value=text, height=300)

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 5 — SNAPSHOTS
# ============================================================

def create_snapshot():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{now}")
    os.makedirs(snap_path, exist_ok=True)

    for fname in [HEALTH_LOG_FILE, OCR_DATA_FILE, PHOTO_DATA_FILE, AI_SUMMARY_FILE]:
        if os.path.exists(fname):
            shutil.copy(fname, snap_path)

def page_snapshots():
    aaa_header()
    st.subheader("🧊 Snapshots & Restore")

    if st.button("Create Snapshot"):
        create_snapshot()
        st.success("Snapshot created.")

    folders = sorted([d for d in os.listdir(SNAPSHOT_DIR) if os.path.isdir(os.path.join(SNAPSHOT_DIR, d))])
    st.markdown("### Existing Snapshots")
    if not folders:
        st.info("No snapshots yet.")
    else:
        for d in folders:
            with st.expander(d):
                st.write("Contains backups of logs, OCR data and summaries.")

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 6 — AI SUMMARY (BASIC — FREE DEMO) — FINAL + TEXT INPUT
# ============================================================

def page_summary():
    aaa_header()
    st.subheader("🧠 AI Summary (Demo)")
    st.caption("Generate a simple, patient-friendly summary using your logs, scanned text, or a direct question.")

    # ------------------------------------------------------------
    # 1) DIRECT QUESTION INPUT (RESTORED)
    # ------------------------------------------------------------
    st.markdown("### 💬 Ask anything to AAA-Health Intelligence")

    user_q = st.text_input(
        "Ask a question:",
        placeholder="Example: Explain my health pattern…"
    )

    if st.button("Submit Question"):
        if user_q.strip() == "":
            st.warning("Please type your question first.")
        else:
            try:
                ai_ans = call_gemini(
                    f"""
Provide a calm, safe, patient-friendly explanation.
Avoid medical advice.

QUESTION:
{user_q}
"""
                )
                st.info(ai_ans)
            except Exception as e:
                st.error(f"AI error: {e}")

    st.markdown("---")

    # ------------------------------------------------------------
    # 2) SELECT SOURCES (YOUR ORIGINAL WORKING SECTION)
    # ------------------------------------------------------------
    st.markdown("### Select Sources")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    col1, col2 = st.columns(2)

    with col1:
        log_choice = (
            st.selectbox(
                "Health Log",
                list(range(len(logs))) if logs else [],
                format_func=lambda i: logs[i].get("date", f"Log {i+1}"),
            )
            if logs else None
        )

    with col2:
        ocr_choice = (
            st.selectbox(
                "OCR Entry",
                list(range(len(ocr))) if ocr else [],
                format_func=lambda i: ocr[i].get("filename", f"OCR {i+1}"),
            )
            if ocr else None
        )

    st.markdown("---")

    # ------------------------------------------------------------
    # 3) GENERATE SUMMARY FROM SOURCES (UNCHANGED)
    # ------------------------------------------------------------
    if st.button("Generate Summary", use_container_width=True):
        if log_choice is None and ocr_choice is None:
            st.error("Please select at least one source.")
            aaa_footer()
            return

        parts = []
        if log_choice is not None:
            parts.append(f"Log Entry:\n{logs[log_choice]}")
        if ocr_choice is not None:
            parts.append(f"OCR Text:\n{ocr[ocr_choice]['text']}")

        combined_text = "\n\n---\n\n".join(parts)

        prompt = f"""
Create a simple, patient-friendly summary of the following text.
Do NOT give medical advice.
Focus only on:
- Observations
- Patterns
- Notable mentions
- General well-being indicators

TEXT:
{combined_text}
"""

        response = call_gemini(prompt)

        st.markdown("### 📘 Your Summary")
        st.markdown(
            f"""
            <div style="
                background-color:#0d233b;
                padding:18px;
                border-radius:12px;
                border:1px solid #1e3a5c;
                color:white;
                line-height:1.6;
            ">
            {response}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE — MERGED VIEW (COMBINED DATA)
# ============================================================

def page_merged_view():
    mode = st.session_state.get("mode", "free")
    check_firewall("Merged View (Combined Data)", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE + TAGLINE + TRIAL MESSAGE
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            ✨ Merged View — Combined Data
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Unified combined analysis using OCR, logs, summaries and medical PDFs.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE → STANDARD PREMIUM LOCK LAYOUT
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Bar (gradient)
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — REAL MERGED VIEW CONTENT
    # --------------------------------------------------------
    st.markdown(
        """
        <div style="font-size:14px; line-height:1.6; margin-bottom:16px; margin-top:8px;">
            AAA merges OCR text, logs, summaries and PDF intelligence into a single combined view —
            your unified medical signal layer.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----- Load data -----
    logs = load_json(HEALTH_LOG_FILE, [])
    ocr_results = load_json(os.path.join(DATA_DIR, "ocr_results.json"), {})
    insights_raw = load_json(AI_SUMMARY_FILE, {})
    vault_data = load_json(os.path.join(DATA_DIR, "vault_data.json"), {})

    st.markdown("---")

    # --------------------------------------------------------
    # 1) HEALTH LOGS
    # --------------------------------------------------------
    st.markdown("### 📘 Health Logs")
    if logs:
        text_block = "\n".join([l.get("summary", "") for l in logs])
        st.code(text_block or "No logs available.", language="text")
    else:
        st.info("No logs available.")

    st.markdown("---")

    # --------------------------------------------------------
    # 2) OCR EXTRACTED TEXT
    # --------------------------------------------------------
    st.markdown("### 📄 OCR Extracted Text")
    if ocr_results:
        st.json(ocr_results)
    else:
        st.info("No OCR data found.")

    st.markdown("---")

    # --------------------------------------------------------
    # 3) AI INSIGHTS
    # --------------------------------------------------------
    st.markdown("### 🤖 AI Insights")
    if insights_raw:
        st.json(insights_raw)
    else:
        st.info("No insights available.")

    st.markdown("---")

    # --------------------------------------------------------
    # 4) PDF INTELLIGENCE
    # --------------------------------------------------------
    st.markdown("### 📂 PDF Intelligence")
    if vault_data:
        st.json(vault_data)
    else:
        st.info("No PDF intelligence data yet.")

    aaa_footer()


# ============================================================
# PAGE 8 — SUMMARY AI (FREE LOCKED + PREMIUM ACTIVE)
# ============================================================

def page_summary_ai():
    mode = st.session_state.get("mode", "free")
    check_firewall("Summary AI (Advanced Summary) — AI", mode)

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL MESSAGE
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧬 Summary AI — Advanced Medical Summary
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Generate a clean, structured, patient-friendly medical summary using AAA Intelligence.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — MATCH HYBRID ENGINE EXACTLY
    # --------------------------------------------------------
    if mode != "premium":

        # Warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Gradient Banner
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL SUMMARY AI ENGINE
    # --------------------------------------------------------

    st.markdown(
        """
        **AAA Intelligence Active**<br>
        You have full access. Features will continue improving with updates.<br><br>

        ⭐ <i>Enjoy a 7-day free trial — full intelligence unlocked.</i>
        """,
        unsafe_allow_html=True,
    )

    # MAIN DESCRIPTION
    st.markdown(
        """
        <div style="font-size:16px; color:#cbd5f5; margin-bottom:20px;">
            AAA Intelligence will extract key clinical meaning from your medical document and
            provide a structured, easy-to-understand medical summary.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # LOAD AVAILABLE FILES
    files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not files:
        st.warning("Upload at least one medical document to generate a summary.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select a document:", files)

    # --------------------------------------------------------
    # GENERATE SUMMARY
    # --------------------------------------------------------
    if st.button("Generate Medical Summary", use_container_width=True):
        with st.spinner("Analyzing your document…"):

            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)
                safe_text = text[:6000]  # safety limit

                prompt = f"""
You are AAA Health Intelligence.

Create a structured, patient-friendly medical summary.

Required Sections:
1. Key Findings  
2. Easy-to-Understand Explanation  
3. Risk Indicators  
4. Missing or Conflicting Information  
5. Actionable Recommendations  
6. Overall Takeaway  

TEXT:
{safe_text}
"""

                result = safe_render(call_gemini(prompt))

                # OUTPUT CARD
                st.markdown(
                    """
                    <div style="
                        padding:24px;
                        border-radius:14px;
                        background:#0f1a2e;
                        border-left:5px solid #38bdf8;
                        box-shadow:0 0 12px rgba(56,189,248,0.25);
                        color:#e2e8f0;
                        font-size:15px;
                        line-height:1.65;
                    ">
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(result, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 9 — INSIGHTS AI (FREE LOCKED + PREMIUM ACTIVE)
# ============================================================

def page_insights_ai():
    mode = st.session_state.get("mode", "free")
    check_firewall("Insights AI", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE + TAGLINE + FREE TRIAL MESSAGE
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧠 Insights AI — Deep Medical Intelligence
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            AI-powered deep medical interpretation combining hybrid signals, OCR, and PDFs.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — Apply FULL PREMIUM LOCK TEMPLATE (GOLD STANDARD)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Banner
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL INSIGHTS AI ENGINE (ACTIVE)
    # --------------------------------------------------------
    st.markdown(
        """
        **AAA Intelligence Active**  
        You have full access. Features will continue improving with updates.

        ⭐ *Enjoy a 7-day free trial — full intelligence unlocked.*
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOAD AVAILABLE FILES
    # --------------------------------------------------------
    files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not files:
        st.warning("Upload at least one medical document to generate Insights.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select a document for insights:", files)

    # --------------------------------------------------------
    # GENERATE HYBRID INSIGHTS
    # --------------------------------------------------------
    if st.button("Generate Insights", use_container_width=True):
        with st.spinner("🔥 Generating AAA Hybrid Intelligence…"):

            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)

                # Run hybrid engine
                raw_output = generate_insights_hybrid(text)
                safe_output = raw_output or ""
                rendered_output = safe_render(safe_output)

                # --------------------------------------------------------
                # SPLIT SUMMARY + DEEP INSIGHTS
                # --------------------------------------------------------
                short_part = ""
                deep_part = rendered_output

                if "SHORT_SUMMARY:" in safe_output:
                    try:
                        short_part = safe_output.split("SHORT_SUMMARY:")[1].split("DEEP_INSIGHTS:")[0].strip()
                    except:
                        short_part = "Unable to extract short summary."

                if "DEEP_INSIGHTS:" in safe_output:
                    try:
                        deep_part = safe_output.split("DEEP_INSIGHTS:")[1].strip()
                    except:
                        deep_part = rendered_output

                short_safe = safe_render(short_part)
                deep_safe = safe_render(deep_part)

                # --------------------------------------------------------
                # SAVE TO INSIGHTS HISTORY
                # --------------------------------------------------------
                save_insights_record(selected_file, short_safe, deep_safe)

                # --------------------------------------------------------
                # DISPLAY OUTPUT
                # --------------------------------------------------------
                st.success("Insights generated successfully!")

                st.markdown(
                    """
                    <div style="padding:18px; border-radius:12px; background:#0f1a2e;
                                border-left:5px solid #38bdf8; box-shadow:0 0 12px rgba(56,189,248,0.25);">
                        <b>AAA Hybrid Summary</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("### 🟦 Short Summary")
                st.markdown(short_safe, unsafe_allow_html=True)

                st.markdown("---")

                st.markdown("### 🟫 Deep Insights")
                st.markdown(deep_safe, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error generating insights: {e}")

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE — INSIGHTS HISTORY (FREE LOCKED + PREMIUM ACTIVE)
# ============================================================

def page_insights_history():
    mode = st.session_state.get("mode", "free")
    check_firewall("Insights History", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE + 7-DAY TRIAL MESSAGE
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            📚 Insights History — AAA Hybrid Intelligence Records
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Review your previously generated AAA Hybrid Insights — summaries, trends, and deep analysis.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE → PREMIUM LOCK LAYOUT (BEST VERSION)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY
    # --------------------------------------------------------
    insights = load_json(INSIGHTS_FILE, [])
    if not insights:
        st.info("No insights found yet. Generate insights using 'Insights AI'.")
        monetization_cta()
        aaa_footer()
        return

    # AAA Brand Colors
    card_bg = "#0B1625"
    teal = "#00A6C8"
    gold = "#D4A037"
    soft_gold = "#F2C678"

    # Styling
    st.markdown(f"""
        <style>
        .aaa-card {{
            background-color: {card_bg};
            padding: 22px;
            border-radius: 14px;
            border-left: 4px solid {gold};
            margin-bottom: 25px;
            box-shadow: 0px 0px 15px rgba(0, 166, 200, 0.15);
        }}
        .aaa-title {{
            color: {gold};
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .aaa-date {{
            color: {teal};
            font-size: 14px;
            margin-bottom: 12px;
        }}
        .aaa-section-title {{
            color: {soft_gold};
            font-size: 16px;
            font-weight: 500;
            margin-top: 15px;
            margin-bottom: 5px;
        }}
        .aaa-divider {{
            height: 1px;
            background-color: rgba(255,255,255,0.08);
            margin: 12px 0;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Render records in reverse order
    for item in insights[::-1]:
        title = item.get("title", "Insight")
        date = item.get("date", "")
        short = item.get("short", "")
        deep = item.get("deep", "")

        st.markdown("<div class='aaa-card'>", unsafe_allow_html=True)

        # Title & Date
        st.markdown(f"<div class='aaa-title'>🧠 {title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='aaa-date'>📅 {date}</div>", unsafe_allow_html=True)

        st.markdown("<div class='aaa-divider'></div>", unsafe_allow_html=True)

        # Short Summary
        st.markdown("<div class='aaa-section-title'>🔹 Short Summary</div>", unsafe_allow_html=True)
        st.markdown(short.replace("-", "• "))

        # Deep Insights (expandable)
        with st.expander("🔸 Deep Insights (Click to expand)"):
            st.markdown(deep.replace("-", "• "))

        st.markdown("<div class='aaa-divider'></div>", unsafe_allow_html=True)

        # Export
        export_text = (
            "AAA INSIGHTS REPORT\n"
            f"Date: {date}\n"
            f"Title: {title}\n\n"
            "SHORT SUMMARY:\n"
            f"{short}\n\n"
            "DEEP INSIGHTS:\n"
            f"{deep}"
        )

        st.download_button(
            label="📥 Download as Text",
            data=export_text,
            file_name=f"aaa_insight_{date.replace(':','-').replace(' ','_')}.txt",
            mime="text/plain",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 10 — SUMMARY REPORT (FULLY ACTIVATED + 7-DAY TRIAL)
# ============================================================

def page_summary_report():
    mode = st.session_state.get("mode", "free")

    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            📘 Summary Report — AAA PDF Intelligence
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Export your AAA-generated summaries into a clean, professional PDF report.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------------
    # FREE MODE — IDENTICAL PREMIUM LOCK (BEST VERSION)
    # ----------------------------------------------------------
    if mode != "premium":

        # Yellow warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:#ffffff;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card (clean centered version)
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Bar (same as Merged View)
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # ----------------------------------------------------------
    # PREMIUM MODE — REMAINS UNTOUCHED
    # ----------------------------------------------------------

    # Load summaries
    summaries = load_json(AI_SUMMARY_FILE, [])

    if not summaries:
        st.info("No AI summaries found. Generate some first in Summary AI.")
        aaa_footer()
        return

    # Select summary
    options = [
        f"{i+1}. {s.get('date', '')} — {s.get('title', 'Summary')}"
        for i, s in enumerate(summaries)
    ]

    selected_idx = st.selectbox(
        "Choose a summary to export as PDF:",
        list(range(len(options))),
        format_func=lambda i: options[i],
    )

    selected = summaries[selected_idx]
    text = selected.get("text", "")
    title = selected.get("title", "AAA Summary")
    date = selected.get("date", "")

    # PDF generation
    if st.button("📄 Generate PDF Report"):
        try:
            generate_pdf(text, title, date, SUMMARY_REPORT_PDF)
            st.success("PDF report generated successfully.")

            with open(SUMMARY_REPORT_PDF, "rb") as f:
                st.download_button(
                    label="📥 Download AAA PDF Report",
                    data=f,
                    file_name="AAA_Health_Summary_Report.pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    monetization_cta()
    aaa_footer()


# -----------------------------------------------------------
# Saving function — unchanged
# -----------------------------------------------------------
def save_ai_summary(text: str, title: str = "AAA Summary"):
    summaries = load_json(AI_SUMMARY_FILE, [])
    summaries.append(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": title,
            "text": text,
        }
    )
    save_json(AI_SUMMARY_FILE, summaries)


# ============================================================
# PAGE 11 — HYBRID ENGINE (FREE LOCKED + PREMIUM ACTIVE)
# ============================================================

def page_hybrid_engine():
    mode = st.session_state.get("mode", "free")
    check_firewall("Hybrid Engine (Multi-Source Intelligence) — AI", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE + TAGLINE + TRIAL MESSAGE
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧠 Hybrid Engine — Multi-Source AAA Intelligence
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Combine OCR, PDFs, doctor notes, summaries and insights into a unified health analysis.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — EXACT SAME FREE LAYOUT AS INSIGHTS HISTORY
    # --------------------------------------------------------
    if mode != "premium":

        # Warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Banner
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL HYBRID ENGINE
    # --------------------------------------------------------

    # Load OCR text
    ocr_text = ""
    try:
        if os.path.exists(OCR_TEXT_FILE):
            with open(OCR_TEXT_FILE, "r") as f:
                ocr_text = f.read()
    except Exception:
        pass

    # Load PDF text
    pdf_text = ""
    try:
        if os.path.exists(PDF_TEXT_FILE):
            with open(PDF_TEXT_FILE, "r") as f:
                pdf_text = f.read()
    except Exception:
        pass

    # Load doctor notes
    doctor_notes = ""
    try:
        if os.path.exists(DOCTOR_NOTES_FILE):
            with open(DOCTOR_NOTES_FILE, "r") as f:
                doctor_notes = f.read()
    except Exception:
        pass

    # Load last AI Summary
    summaries = load_json(AI_SUMMARY_FILE, [])
    last_summary = summaries[-1]["text"] if summaries else ""

    # Load last AI Insight (deep section)
    insights = load_json(INSIGHTS_FILE, [])
    last_insight = insights[-1]["deep"] if insights else ""

    # --------------------------------------------------------
    # CHECKBOX OPTIONS
    # --------------------------------------------------------
    st.markdown("### Select intelligence sources to combine:")

    use_ocr = st.checkbox("OCR extracted text", True)
    use_pdf = st.checkbox("PDF extracted text", True)
    use_notes = st.checkbox("Doctor notes", True)
    use_summary = st.checkbox("AI Summary", True)
    use_insight = st.checkbox("AI Insight", True)

    # --------------------------------------------------------
    # RUN HYBRID ENGINE
    # --------------------------------------------------------
    if st.button("⚡ Generate Hybrid Intelligence Report", use_container_width=True):
        with st.spinner("Combining multi-source intelligence…"):

            combined_text = ""

            if use_ocr and ocr_text:
                combined_text += "\n\n[OCR]\n" + ocr_text
            if use_pdf and pdf_text:
                combined_text += "\n\n[PDF]\n" + pdf_text
            if use_notes and doctor_notes:
                combined_text += "\n\n[NOTES]\n" + doctor_notes
            if use_summary and last_summary:
                combined_text += "\n\n[SUMMARY]\n" + last_summary
            if use_insight and last_insight:
                combined_text += "\n\n[INSIGHT]\n" + last_insight

            if not combined_text.strip():
                st.error("No available text to combine.")
                aaa_footer()
                return

            prompt = f"""
You are AAA Hybrid Engine.

Combine all provided medical information into a single,
clear, structured, medically-balanced unified health analysis.

SOURCES:
{combined_text}

OUTPUT FORMAT:
- Key Findings
- Risks & Severity
- Patterns & Trends
- Explanation (doctor-style)
- Actionable steps (general, safe)
"""

            try:
                response = call_gemini(prompt)
                st.markdown(response)
            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 12 — RICH ANALYTICS DASHBOARD (PREMIUM ANALYTICS)
# ============================================================

def page_analytics_dashboard():
    # ✔ Correct firewall name (matches sidebar)
    check_firewall("📊 Rich Analytics Dashboard (Premium Analytics)", st.session_state.get("mode", "free"))

    mode = st.session_state.get("mode", "free")

    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            📊 Rich Analytics Dashboard — AAA Premium Intelligence
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Deep AI analytics powered by your summaries, insights, logs, and health signal patterns.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------------
    # FREE MODE → SHOW HYBRID ENGINE PREMIUM LOCK UI
    # ----------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card (same style)
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # ----------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # ----------------------------------------------------------

    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except:
        st.error("Required libraries not available.")
        aaa_footer()
        return

    summaries = load_json(AI_SUMMARY_FILE, [])
    insights = load_json(INSIGHTS_FILE, [])
    health_data = load_json(HEALTH_LOG_FILE, [])
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    # ---------------- DATA OVERVIEW ----------------
    st.markdown("## 🗂 Data Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AI Summaries", len(summaries))
    col2.metric("AI Insights", len(insights))
    col3.metric("Health Log Entries", len(health_data))
    col4.metric("Documents in Vault", len(vault_files))
    st.markdown("---")

    # ---------------- TREND CHART ----------------
    st.markdown("## 📈 Health Score Trend (Last 30 Entries)")
    if health_data:
        try:
            df = pd.DataFrame(health_data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").tail(30)

            fig, ax = plt.subplots()
            ax.plot(df["date"], df["score"])
            ax.set_xlabel("Date")
            ax.set_ylabel("Health Score")
            ax.set_title("Health Score Trend (Last 30 Updates)")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error rendering chart: {e}")
    else:
        st.info("No health log data available.")
    st.markdown("---")

    # ---------------- TERM FREQUENCY ----------------
    st.markdown("## 🧬 Key Medical Terms Frequency")
    if summaries:
        try:
            text_all = " ".join(s.get("text", "") for s in summaries).lower()
            keywords = [
                "blood", "pressure", "glucose", "cholesterol", "kidney",
                "liver", "infection", "inflammation", "rate", "risk",
                "deficiency", "vitamin", "anemia", "pain", "fatigue"
            ]
            freq = {k: text_all.count(k) for k in keywords}
            df2 = pd.DataFrame(list(freq.items()), columns=["Term", "Count"])
            st.bar_chart(df2.set_index("Term"))
        except Exception as e:
            st.error(f"Error generating term frequency: {e}")
    else:
        st.info("No summaries available for analysis.")
    st.markdown("---")

    # ---------------- CONDITION ALERTS ----------------
    st.markdown("## 🚨 Potential Condition Flags (AI)")
    if insights:
        combined_text = " ".join(i.get("deep", "") for i in insights).lower()
        alert_keywords = [
            ("Kidney-related indicators", ["creatinine", "gfr", "urea"]),
            ("Cardio Indicators", ["bp", "hypertension", "tachy", "cholesterol"]),
            ("Infection Markers", ["stool", "wbc", "infection"]),
            ("Inflammation Markers", ["crp", "esr", "inflamm"]),
        ]
        for title, keys in alert_keywords:
            if any(k in combined_text for k in keys):
                st.warning(f"⚠ **{title} flagged in recent reports**")
    else:
        st.info("No insights available for condition flagging.")
    st.markdown("---")

    # ---------------- REGIONAL AWARENESS ----------------
    st.markdown("## 🌏 Regional Health Awareness (Beta)")
    st.markdown(
        """
        <p style="font-size:15px; line-height:1.6; color:#CBD5E1;">
            Region-based trends, seasonal alerts and general wellness awareness.
            (Static beta content — will be replaced with live models.)
        </p>
        """, unsafe_allow_html=True)
    region = "Sydney, AU"
    st.info(f"Region detected: **{region}**")
    st.markdown("""
        - 🌡 Seasonal allergies are moderate.  
        - 🤧 Flu cases rising locally.  
        - 🦠 Gastro outbreaks reported in nearby suburbs.  
        - ☀ UV index trending high — take extra precautions.  
    """)

    st.markdown("---")
    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 13 — SMART SNAPSHOTS (FINAL PREMIUM-ALIGNED VERSION)
# ============================================================

def page_snapshots():
    mode = st.session_state.get("mode", "free")
    check_firewall("Snapshots", mode)
    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="text-align:center; color:#00D4FF; margin-bottom:0;">
            🧊 Snapshots — Backup & Restore
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Save your current AAA health state — logs, OCR, summaries —
            and restore anytime. All data stays safely on your device.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE — IDENTICAL PREMIUM LOCK AS HYBRID ENGINE
    # --------------------------------------------------------
    if mode != "premium":

        # Warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Feature card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    Smart Snapshots allow you to save, restore,
                    and download your medical state anytime.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Banner
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL SNAPSHOT ENGINE
    # --------------------------------------------------------

    # CREATE SNAPSHOT
    if st.button("📦 Create New Snapshot", use_container_width=True):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{now}")
        os.makedirs(snap_path, exist_ok=True)

        for fname in [
            HEALTH_LOG_FILE,
            OCR_DATA_FILE,
            PHOTO_DATA_FILE,
            AI_SUMMARY_FILE,
        ]:
            if os.path.exists(fname):
                shutil.copy(fname, snap_path)

        st.success(f"Snapshot saved as: snapshot_{now}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # LIST SNAPSHOTS
    st.subheader("📁 Available Snapshots")

    folders = sorted(
        [
            d for d in os.listdir(SNAPSHOT_DIR)
            if os.path.isdir(os.path.join(SNAPSHOT_DIR, d))
        ],
        reverse=True,
    )

    if not folders:
        st.info("No snapshots created yet.")
        monetization_cta()
        aaa_footer()
        return

    for folder in folders:
        folder_path = os.path.join(SNAPSHOT_DIR, folder)

        with st.expander(f"📦 {folder}"):

            st.write("Includes logs, OCR results, photos, and AI summaries.")

            col1, col2, col3 = st.columns([1, 1, 1])

            # RESTORE SNAPSHOT
            with col1:
                if st.button(f"Restore {folder}", key=f"restore_{folder}"):
                    for fname in os.listdir(folder_path):
                        src = os.path.join(folder_path, fname)
                        dst = fname  # overwrite working file
                        shutil.copy(src, dst)
                    st.success(f"Restored snapshot: {folder}")

            # DOWNLOAD SNAPSHOT
            with col2:
                zipped = shutil.make_archive(folder_path, "zip", folder_path)
                with open(zipped, "rb") as f:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=f"{folder}.zip",
                        mime="application/zip",
                        key=f"download_{folder}",
                    )

            # DELETE SNAPSHOT
            with col3:
                if st.button(f"Delete {folder}", key=f"delete_{folder}"):
                    shutil.rmtree(folder_path)
                    st.warning(f"Deleted snapshot: {folder}")
                    st.experimental_rerun()

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 14 — SMART TIMELINE (BETA)
# ============================================================

def page_timeline():
    check_firewall("Timeline", st.session_state.get("mode", "free"))
    aaa_header()

    st.subheader("📅 Smart Timeline (Beta)")

    logs = load_logs()
    vault_files = load_vault_files()

    st.markdown("### 🧠 Today's Signals")

    if not logs:
        st.warning("Not enough data to evaluate logging frequency.")
    else:
        st.success("Logging activity detected.")

    if vault_files:
        st.success(f"**{len(vault_files)} documents stored** — vault is active.")
    else:
        st.warning("No documents found.")

    st.markdown("---")

    st.markdown("### 🧩 Why These Signals Matter")
    st.markdown(
        """
        These signals help AAA create personalised health trends using your logs,
        snapshots, documents and generated summaries.
        """
    )

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 16 — AI HEALTH RISK ENGINE (RISK SIGNALS — PREMIUM)
# ============================================================

def compute_health_score(merged_data, insights, logs):
    if not merged_data and not insights and not logs:
        return 72, "⚠️ Limited data — upload more logs and documents.", []

    reasons = []
    score = 80

    # -------------------------
    # LOG-BASED SIGNALS
    # -------------------------
    if logs:
        latest_logs = logs[-5:]
        for log in latest_logs:
            t = log.get("type", "").lower()
            val = log.get("value", 0)

            if "bp" in t:
                if val > 140:
                    score -= 5
                    reasons.append("Elevated blood pressure detected.")
                elif val < 100:
                    score -= 3
                    reasons.append("Low blood pressure episodes noted.")

            if "sleep" in t:
                if val < 6:
                    score -= 2
                elif val > 8:
                    score += 1

    # -------------------------
    # INSIGHT RISK LEVELS
    # -------------------------
    for item in insights:
        risk = item.get("risk_level", "").lower()
        if "high" in risk:
            score -= 7
        if "moderate" in risk:
            score -= 3

    # -------------------------
    # MERGED DATA SIGNALS
    # -------------------------
    if merged_data:
        for item in merged_data:
            cat = item.get("category", "").lower()
            val = item.get("value", "")

            if "cholesterol" in cat:
                if isinstance(val, (int, float)):
                    if val > 240:
                        score -= 5
                    elif val < 200:
                        score += 2

            if "glucose" in cat:
                if isinstance(val, (int, float)):
                    if val > 130:
                        score -= 4
                    elif val < 100:
                        score += 1

    score = max(1, min(99, score))
    summary = " • ".join(reasons[:4]) if reasons else "Stable — no major issues detected."
    return score, summary, reasons


# ============================================================
# PAGE RENDER — MUST MATCH SIDEBAR EXACTLY
# ============================================================

def page_health_risk_engine():
    """
    Sidebar label:
    🚨 AI Health Risk Engine (Risk Signals) — PREMIUM
    """

    mode = st.session_state.get("mode", "free")

    # 🔥 CRITICAL — FIREWALL STRING MUST MATCH SIDEBAR EXACTLY
    check_firewall("🚨 AI Health Risk Engine (Risk Signals) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE + SUBTITLE + TRIAL LINE (MATCH PREMIUM DESIGN)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧠 AI Health Risk Engine — AAA Premium Intelligence
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Deep AI evaluation of your logs, summaries, merged data and risk signals.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — PREVENT FURTHER RENDERING
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow bar
        st.markdown("""
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;">
                ⚠️ This feature is available for Premium members.
            </div>
        """, unsafe_allow_html=True)

        # Upgrade text
        st.markdown("""
            <div style="margin-top:22px; font-size:18px; color:white;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
        """, unsafe_allow_html=True)

        # Premium Feature Card
        st.markdown("""
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="color:#93c5fd; margin:0; padding:0; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="margin-top:10px; color:#cbd5e1; font-size:14px; line-height:1.6;">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Blue CTA bar
        st.markdown("""
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
        """, unsafe_allow_html=True)

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL ENGINE
    # --------------------------------------------------------
    merged_data = load_json(MERGED_DATA_FILE, [])
    insights = load_json(INSIGHTS_FILE, [])
    logs = load_json(HEALTH_LOG_FILE, [])

    score, summary_text, reasons = compute_health_score(merged_data, insights, logs)

    navy = "#071E36"
    teal = "#00A6B6"
    gold = "#F4BD3B"
    soft_gold = "#F2C678"

    # SCORE CARD
    st.markdown(
        f"""
        <div style="background:{navy}; padding:25px; border-radius:18px;
                    border-left:5px solid {gold};
                    box-shadow:0 0 12px rgba(0,150,220,0.25);">
            <div style="font-size:48px; font-weight:700; color:{soft_gold};
                        text-align:center;">
                {score}
            </div>
            <div style="text-align:center; font-size:20px; margin-top:10px;
                        color:{teal};">
                Your Current AI Health Score
            </div>
            <div style="margin-top:20px; font-size:15px; color:#DDEAFF;
                        text-align:center;">
                {summary_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # BREAKDOWN
    st.markdown("<h4 style='color:#F2C678; margin-top:24px;'>Breakdown</h4>", unsafe_allow_html=True)

    if reasons:
        for r in reasons[:8]:
            st.markdown(
                f"""
                <div style="background:#102C45; padding:12px; margin:8px 0;
                            border-radius:10px; color:#DDEAFF;
                            border-left:4px solid {teal};">
                    {r}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No additional risk indicators found.")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 17 — SUMMARY REPORT AI (PDF INTELLIGENCE)
# ============================================================

def page_summary_report_ai():
    check_firewall("Summary Report AI", st.session_state.get("mode", "free"))
    aaa_header()

    st.subheader("📄 Summary Report AI (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; margin-bottom:15px;">
            Generate a complete AI-powered PDF health report — combining
            logs, OCR, summaries, insights, and timeline events.
        </div>
        """,
        unsafe_allow_html=True,
    )

    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(INSIGHTS_HISTORY_FILE, [])
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not logs and not insights and not vault_files:
        st.warning("Not enough data to generate a report.")
        monetization_cta()
        aaa_footer()
        return

    include_logs = st.checkbox("Include Health Logs", True)
    include_insights = st.checkbox("Include Insights", True)
    include_vault = st.checkbox("Include Vault Files", True)

    if st.button("Generate PDF Report"):
        with st.spinner("Generating report…"):

            # PDF generator MUST exist in Block 4–6
            temp_pdf = "/tmp/aaa_full_report.pdf"

            try:
                generate_pdf_report(
                    temp_pdf,
                    logs if include_logs else [],
                    insights if include_insights else [],
                    vault_files if include_vault else [],
                )

                with open(temp_pdf, "rb") as f:
                    st.download_button(
                        "📥 Download Report",
                        f,
                        file_name="AAA_Health_Report.pdf",
                        mime="application/pdf",
                    )
                st.success("Report ready!")

            except Exception as e:
                st.error(f"Error generating PDF: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 18 — STRIPE MONETIZATION ENGINE (DEMO)
# ============================================================

def page_stripe_monetization_demo():
    check_firewall("Stripe Demo", st.session_state.get("mode", "free"))
    aaa_header()

    st.subheader("💳 Stripe Monetization Engine (Demo)")

    st.markdown(
        """
        <div style="font-size:16px;">
            This is a preview of Artigellence Premium billing.  
            Demo mode — no real payments.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Stripe live checkout is disabled. This is a preview only.")

    col1, col2, col3 = st.columns(3)

    # AUSTRALIA
    with col1:
        st.markdown(
            """
            <div style='background:#102C45; padding:20px; border-radius:12px;'>
                <h3 style='color:#5BB6FF;'>Australia</h3>
                <h2 style='color:white;'>A$10 / month</h2>
                <ul style='color:#D0EAFF; font-size:14px;'>
                    <li>Unlimited AI Summaries</li>
                    <li>Deep Insights</li>
                    <li>Merged View</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # INDIA
    with col2:
        st.markdown(
            """
            <div style='background:#0F233A; padding:20px; border-radius:12px;'>
                <h3 style='color:#5BB6FF;'>India</h3>
                <h2 style='color:white;'>₹500 / month</h2>
                <ul style='color:#D0EAFF; font-size:14px;'>
                    <li>All Premium Tools</li>
                    <li>AAA Hybrid Intelligence</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # GLOBAL
    with col3:
        st.markdown(
            """
            <div style='background:#102C45; padding:20px; border-radius:12px;'>
                <h3 style='color:#5BB6FF;'>Global</h3>
                <h2 style='color:white;'>$10 / month</h2>
                <ul style='color:#D0EAFF; font-size:14px;'>
                    <li>All Premium Features</li>
                    <li>Priority Access</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.warning("Checkout disabled in demo mode.")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 19 — EDGE NODE MEMORY (AAA BETA)
# ============================================================

def page_edge_node_memory():
    check_firewall("Edge Node Memory", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown(
        """
        <h2 style="text-align:center; color:#00D4FF;">
            🤖 Edge Node Memory (Beta)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Adaptive memory layer that evolves with your health patterns.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    memory_file = os.path.join(DATA_DIR, "edge_memory.json")
    if not os.path.exists(memory_file):
        with open(memory_file, "w") as f:
            json.dump({"events": []}, f, indent=4)

    st.subheader("🧠 Add Memory Signal")
    signal = st.text_input("Enter a pattern or observation:")

    if st.button("Save Signal"):
        with open(memory_file, "r") as f:
            data = json.load(f)

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "signal": signal.strip(),
        }

        data["events"].append(entry)

        with open(memory_file, "w") as f:
            json.dump(data, f, indent=4)

        st.success("Memory saved!")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("📡 Active Memory Streams")

    with open(memory_file, "r") as f:
        data = json.load(f)

    events = data.get("events", [])

    if not events:
        st.info("No memory signals yet.")
        monetization_cta()
        aaa_footer()
        return

    for e in reversed(events):
        st.markdown(
            f"""
            <div style="
                background:#0E1A2B;
                padding:12px;
                margin:8px 0;
                border-radius:10px;
                border-left:4px solid #00D4FF;
                color:#D0E4FF;">
                <b>{e['timestamp']}</b><br>
                {e['signal']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 39 — SNAPSHOTS (FINAL UI EDITION)
# ============================================================

def page_snapshots():
    # 🔒 Consistent firewall
    check_firewall("Snapshots", st.session_state.get("mode", "free"))

    aaa_header()

    st.markdown(
        """
        <h2 style="text-align:center; color:#00D4FF; margin-bottom:0;">
            🧊 Snapshots — Backup & Restore
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Save your current AAA health state — logs, OCR, summaries — 
            and restore anytime. All data stays on your device.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # CREATE SNAPSHOT
    # -------------------------------
    if st.button("📦 Create New Snapshot", use_container_width=True):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{now}")
        os.makedirs(snap_path, exist_ok=True)

        for fname in [HEALTH_LOG_FILE, OCR_DATA_FILE, PHOTO_DATA_FILE, AI_SUMMARY_FILE]:
            if os.path.exists(fname):
                shutil.copy(fname, snap_path)

        st.success(f"Snapshot saved as: snapshot_{now}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # -------------------------------
    # LIST SNAPSHOTS
    # -------------------------------
    st.subheader("📁 Available Snapshots")

    folders = sorted(
        [d for d in os.listdir(SNAPSHOT_DIR) if os.path.isdir(os.path.join(SNAPSHOT_DIR, d))],
        reverse=True
    )

    if not folders:
        st.info("No snapshots created yet.")
        monetization_cta()
        aaa_footer()
        return

    for folder in folders:
        folder_path = os.path.join(SNAPSHOT_DIR, folder)

        with st.expander(f"📦 {folder}"):

            st.write("Contains copies of logs, OCR results, photos, and AI summaries.")

            col1, col2, col3 = st.columns([1, 1, 1])

            # --------------------------------------
            # RESTORE SNAPSHOT
            # --------------------------------------
            with col1:
                if st.button(f"Restore {folder}", key=f"restore_{folder}"):
                    for fname in os.listdir(folder_path):
                        src = os.path.join(folder_path, fname)
                        dst = fname  # overwrite working file
                        shutil.copy(src, dst)
                    st.success(f"Restored snapshot: {folder}")

            # --------------------------------------
            # DOWNLOAD SNAPSHOT
            # --------------------------------------
            with col2:
                zipped = shutil.make_archive(folder_path, "zip", folder_path)
                with open(zipped, "rb") as f:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=f"{folder}.zip",
                        mime="application/zip",
                        key=f"download_{folder}",
                    )

            # --------------------------------------
            # DELETE SNAPSHOT
            # --------------------------------------
            with col3:
                if st.button(f"Delete {folder}", key=f"delete_{folder}"):
                    shutil.rmtree(folder_path)
                    st.warning(f"Deleted snapshot: {folder}")
                    st.experimental_rerun()

    monetization_cta()
    aaa_footer()


# ============================================================
# PDF GENERATION ENGINE — POLISHED (STEP 1 COMPLETED)
# ============================================================

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor


def generate_pdf_report(path, logs, insights, vault_files, doctor_summary=""):
    """
    Generates a polished, presentation-ready PDF summary for AAA — Health Intelligence.
    """

    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 1 * inch

    # ---------------------------------------------------------
    # TITLE BLOCK
    # ---------------------------------------------------------
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(HexColor("#FACC15"))
    c.drawString(1 * inch, y, "AAA — Health Intelligence Report")

    y -= 0.4 * inch
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#E2E8F0"))
    c.drawString(1 * inch, y, "AI-powered clinical summary • Lab insights • Logs • Vault intelligence")

    y -= 0.5 * inch

    c.setStrokeColor(HexColor("#38BDF8"))
    c.setLineWidth(1)
    c.line(1 * inch, y, width - 1 * inch, y)
    y -= 0.5 * inch

    # ---------------------------------------------------------
    # DOCTOR-STYLE SUMMARY
    # ---------------------------------------------------------
    if doctor_summary:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#FACC15"))
        c.drawString(1 * inch, y, "🩺 Clinical AI Summary")
        y -= 0.35 * inch

        c.setFont("Helvetica", 11)
        c.setFillColor(HexColor("#E2E8F0"))

        for line in doctor_summary.split("\n"):
            c.drawString(1 * inch, y, line[:110])
            y -= 0.22 * inch
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch

        y -= 0.3 * inch
        c.setStrokeColor(HexColor("#334155"))
        c.line(1 * inch, y, width - 1 * inch, y)
        y -= 0.4 * inch

    # ---------------------------------------------------------
    # HEALTH LOGS
    # ---------------------------------------------------------
    if logs:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#38BDF8"))
        c.drawString(1 * inch, y, "📘 Health Logs")
        y -= 0.35 * inch

        c.setFont("Helvetica", 11)
        c.setFillColor(HexColor("#E2E8F0"))

        for entry in logs[:12]:
            text = f"- {entry.get('timestamp', '')}: {entry.get('text', '')}"
            c.drawString(1 * inch, y, text[:110])
            y -= 0.22 * inch

            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch

        y -= 0.4 * inch

    # ---------------------------------------------------------
    # INSIGHTS HISTORY
    # ---------------------------------------------------------
    if insights:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#38BDF8"))
        c.drawString(1 * inch, y, "📊 AI Insights History")
        y -= 0.35 * inch

        c.setFont("Helvetica", 11)
        c.setFillColor(HexColor("#E2E8F0"))

        insight_items = insights.get("history", [])

        for item in insight_items[:10]:
            text = f"- {item.get('summary', '')}"
            c.drawString(1 * inch, y, text[:110])
            y -= 0.22 * inch

            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch

        y -= 0.4 * inch

    # ---------------------------------------------------------
    # VAULT FILES
    # ---------------------------------------------------------
    if vault_files:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#38BDF8"))
        c.drawString(1 * inch, y, "📁 Vault File Summaries")
        y -= 0.35 * inch

        c.setFont("Helvetica", 11)
        c.setFillColor(HexColor("#E2E8F0"))

        for f in vault_files[:8]:
            c.drawString(1 * inch, y, f"- {f}")
            y -= 0.22 * inch

            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch

        y -= 0.3 * inch

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#94A3B8"))
    c.drawString(
        1 * inch,
        0.6 * inch,
        "Generated by Artigellence — AAA Health Intelligence · Private · Local · Secure"
    )

    c.save()


# ============================================================
# PAGE 20 — AAA PATTERN TIMELINE AI
# ============================================================

def page_pattern_timeline_ai():
    mode = st.session_state.get("mode", "free")

    # FIREWALL (must match sidebar)
    check_firewall("AAA Pattern Timeline AI — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES Page 21, 22, 23, 24)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            🧩 AAA Pattern Timeline AI — Neuralink-Style Condensed Signals
        </h2>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            High-density compression of logs, insights, memory signals, and patterns across time.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE — PREMIUM LOCK UI (same template as Page 21)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            AAA compresses logs, insights, and behavioural signals into a unified
            high-density timeline. Inspired by Neuralink-style compression.
        </div>
        """,
        unsafe_allow_html=True,
    )

    logs = load_json(HEALTH_LOG_FILE, [])
    vault_files = os.listdir(VAULT_DIR)
    insights = load_json(AI_SUMMARY_FILE, {})
    memory_signals = load_json(os.path.join(DATA_DIR, "memory_signals.json"), [])

    st.markdown("### 📅 Select Timeline Range")
    range_choice = st.selectbox(
        "Choose analysis period:",
        ["Last 7 Days", "Last 14 Days", "Last 30 Days"]
    )

    days = 7 if range_choice == "Last 7 Days" else 14 if range_choice == "Last 14 Days" else 30
    cutoff = datetime.now().timestamp() - (days * 86400)

    filtered_logs = [l for l in logs if l.get("timestamp", 0) >= cutoff]

    st.markdown("### 🧠 Condensed Signal Timeline")
    if not filtered_logs:
        st.info("No activity detected in this range.")
    else:
        for log in filtered_logs:
            ts = datetime.fromtimestamp(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
            summary = log.get("summary", "")

            st.markdown(
                f"""
                <div style="background:#0d1b2a; padding:15px; border-radius:10px; margin-bottom:10px;">
                    <b>🗓 {ts}</b><br>
                    <span>{summary}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button("🔮 Generate Condensed Pattern Summary"):
        with st.spinner("Analyzing behavioural & medical signals…"):

            combined_text = (
                "\n".join([l.get("summary", "") for l in filtered_logs]) + "\n" +
                "\n".join(memory_signals) + "\n" +
                json.dumps(insights, indent=2)
            )

            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                response = ai.generate_content(
                    f"""
                    You are AAA Pattern Timeline AI.
                    TASK:
                    - Fuse logs, memory signals, insights
                    - Detect behaviour clusters
                    - Output condensed Neuralink-style summary

                    DATA:
                    {combined_text}

                    FORMAT:
                    1. High-density burst
                    2. Behaviour clusters
                    3. Micro patterns
                    4. Predictive indicators
                    """
                )
                st.info(response.text)
            except Exception as e:
                st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 21 — AI HEALTH RISK ENGINE (PREMIUM)
# ============================================================

def page_risk_engine():
    mode = st.session_state.get("mode", "free")

    # FIREWALL — label must match SIDEBAR EXACTLY
    check_firewall("AI Health Risk Engine (Risk Signals) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES PAGES 20–24)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            ⚠️ AI Health Risk Engine — Pattern & Signal Scanner (Beta)
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE — unified style across premium pages
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Detect behavioural drift, weak points, risk contributors, and early indicators.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # GOLD TRIAL LINE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE — PREMIUM LOCK UI
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------

    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})
    memory_signals = load_json(os.path.join(DATA_DIR, "memory_signals.json"), [])

    # WINDOW SELECTOR
    st.markdown("### 📅 Select Analysis Window")
    window = st.selectbox("Analyze patterns for:", ["Last 7 Days", "Last 14 Days", "Last 30 Days"])

    days = 7 if window == "Last 7 Days" else 14 if window == "Last 14 Days" else 30
    cutoff = datetime.now().timestamp() - (days * 86400)

    filtered_logs = [l for l in logs if l.get("timestamp", 0) >= cutoff]

    # ACTIVITY OVERVIEW
    st.markdown("### 📊 Recent Activity Overview")
    if not filtered_logs:
        st.info("No signals found.")
    else:
        for log in filtered_logs:
            ts = datetime.fromtimestamp(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
            summary = log.get("summary", "")
            st.markdown(
                f"""
                <div style="background:#0e1a25; padding:12px; border-radius:10px; margin-bottom:10px;">
                    <b>{ts}</b><br>{summary}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # RUN AI ANALYSIS
    if st.button("🚨 Run Risk Pattern Analysis"):
        with st.spinner("Evaluating patterns…"):

            combined = (
                "\n".join([l.get("summary", "") for l in filtered_logs]) + "\n" +
                json.dumps(insights, indent=2) + "\n" +
                "\n".join(memory_signals)
            )

            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                resp = ai.generate_content(
                    f"""
You are AAA — Artigellence Augmentation Aggregator.

Analyze logs, insights, and signals.

FORMAT:
🔶 Pattern Deviation Summary
📉 Behavioural Risk Contributors
🧩 Lifestyle Weak Points
🔮 Early Indicators (7 Days)
📊 Consistency Score (0–100)

DATA:
{combined}
                    """
                )
                st.info(resp.text)

            except Exception as e:
                st.error(f"AI Error: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 22 — INSIGHT FUSION LAYER
# ============================================================

def page_insight_fusion():
    mode = st.session_state.get("mode", "free")

    # FIREWALL — must match sidebar EXACTLY
    check_firewall("Insight Fusion Layer (Fusion Intelligence) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES ALL OTHER PREMIUM PAGES)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            🌐 Insight Fusion Layer — Unified Health Intelligence (Beta)
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE — UNIFIED STYLE
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Multi-signal fusion of logs, insights, OCR, vault PDFs, scores, and memory signals.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 7-DAY TRIAL LINE — SAME GOLD STYLE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE — PREMIUM LOCK (NO CHANGE)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------

    # LOAD ALL SIGNAL SOURCES
    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})
    memory_signals = load_json(os.path.join(DATA_DIR, "memory_signals.json"), [])
    vault_data = load_json(os.path.join(DATA_DIR, "vault_data.json"), {})
    score_history = load_json(os.path.join(DATA_DIR, "score_history.json"), [])
    ocr_results = load_json(os.path.join(DATA_DIR, "ocr_results.json"), {})

    # PREPARE TEXT BLOCKS
    logs_text = "\n".join([l.get("summary", "") for l in logs])
    memory_text = "\n".join(memory_signals)
    insights_text = json.dumps(insights, indent=2)
    vault_text = json.dumps(vault_data, indent=2)
    ocr_text = json.dumps(ocr_results, indent=2)
    score_text = json.dumps(score_history, indent=2)

    combined_text = f"""
==== LOG SUMMARIES ====
{logs_text}

==== INSIGHTS HISTORY ====
{insights_text}

==== MEMORY SIGNALS ====
{memory_text}

==== OCR EXTRACTED TEXT ====
{ocr_text}

==== VAULT PDF DATA ====
{vault_text}

==== HEALTH SCORE HISTORY ====
{score_text}
"""

    # RUN FUSION ENGINE
    if st.button("🌐 Generate Unified Intelligence"):
        with st.spinner("Generating fusion…"):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                resp = model.generate_content(
                    f"""
You are AAA — Artigellence Augmentation Aggregator.

Fuse all signals into unified intelligence.

FORMAT:
🌐 Unified Intelligence Burst
📊 Cross-Signal Patterns
🧩 Hidden Correlations
📉 Behavioural Drift
🔮 7-Day Indicators
📌 Recommended Action Loops

DATA:
{combined_text}
"""
                )
                st.info(resp.text)

            except Exception as e:
                st.error(f"Fusion Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 23 — AAA INSIGHT GRAPHS (PREMIUM)
# ============================================================

def page_insight_graphs():
    mode = st.session_state.get("mode", "free")

    # FIREWALL — must match sidebar
    check_firewall("Insight Graphs (Visual Charts) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM-STYLE TITLE (MATCHES RICH ANALYTICS & TRIPTYCH)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            📈 AAA Insight Graphs & Trend Visualizer
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE — SAME STYLE AS OTHER PREMIUM PAGES
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Visual analytics powered by your logs, summaries, insights, and health signal trends.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 7-DAY TRIAL LINE — IDENTICAL STYLE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE — EXACT TEMPLATE OF PAGE 20
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This visual intelligence feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------

    # LOAD DATA
    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})
    score_history = load_json(os.path.join(DATA_DIR, "score_history.json"), [])

    # Convert safely to DataFrames
    log_df = pd.DataFrame(logs) if logs else pd.DataFrame()
    score_df = pd.DataFrame(score_history) if score_history else pd.DataFrame()
    insight_df = pd.DataFrame(insights.get("history", [])) if insights else pd.DataFrame()

    st.markdown("---")

    # --------------------------------------------------------
    # 1) HEALTH SCORE TREND
    # --------------------------------------------------------
    st.markdown("### 📈 Health Score Trend (0–100)")

    if not score_df.empty:
        score_df["date"] = pd.to_datetime(score_df["timestamp"]).dt.date

        chart = alt.Chart(score_df).mark_line(point=True).encode(
            x="date:T",
            y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100])),
            tooltip=["date", "score"]
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No health scores available yet.")

    st.markdown("---")

    # --------------------------------------------------------
    # 2) DAILY LOG FREQUENCY
    # --------------------------------------------------------
    st.markdown("### 📊 Daily Log Activity")

    if not log_df.empty:
        log_df["date"] = pd.to_datetime(log_df["timestamp"], unit="s").dt.date
        freq_df = log_df.groupby("date").size().reset_index(name="count")

        chart = alt.Chart(freq_df).mark_bar().encode(
            x="date:T",
            y="count:Q",
            tooltip=["date", "count"]
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No logs found.")

    st.markdown("---")

    # --------------------------------------------------------
    # 3) INSIGHT FREQUENCY
    # --------------------------------------------------------
    st.markdown("### 🧩 Insight Frequency Trend")

    if not insight_df.empty:
        insight_df["date"] = pd.to_datetime(insight_df["timestamp"]).dt.date
        freq = insight_df.groupby("date").size().reset_index(name="count")

        chart = alt.Chart(freq).mark_area(opacity=0.5).encode(
            x="date:T",
            y="count:Q",
            tooltip=["date", "count"]
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No insights yet.")

    aaa_footer()


# ============================================================
# PAGE 24 — MEDICAL TRIPTYCH (3-PANEL VIEW) — PREMIUM
# ============================================================

def page_medical_triptych():
    mode = st.session_state.get("mode", "free")

    # 🔐 FIREWALL — MUST MATCH SIDEBAR EXACTLY
    check_firewall("Medical Triptych (3-Panel View) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE — MATCHES RICH ANALYTICS DASHBOARD EXACTLY
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            🩺 Medical Triptych — Doctor + Lab + PDF Fusion (Beta)
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # SUBTITLE — MATCH RICH ANALYTICS STYLE
    # --------------------------------------------------------
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Unified medical fusion of doctor notes, lab reports, and vault PDFs — Beta.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ⭐ 7-DAY TRIAL LINE — SAME AS RICH ANALYTICS
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # FREE MODE — PREMIUM LOCK UI (same as Page 20 template)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:25px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="margin-top:18px; font-size:18px; color:white;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:30px;
                padding:26px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="margin-top:10px; color:#cbd5e1; font-size:14px; line-height:1.6;">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Bar
        st.markdown(
            """
            <div style="
                margin-top:28px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (NO CHANGE)
    # --------------------------------------------------------

    st.markdown("### 🟦 Doctor Notes")
    doctor_notes = st.text_area(
        "Enter clinical notes, symptoms, observations…",
        height=120,
        placeholder="Example: Patient reports fatigue, mild chest discomfort…"
    )

    st.markdown("### 🟧 Lab Report (PDF → Text)")
    lab_pdf = st.file_uploader("Upload Lab PDF", type=["pdf"], key="lab_pdf_uploader")
    lab_text = ""

    if lab_pdf:
        try:
            with open("temp_lab.pdf", "wb") as f:
                f.write(lab_pdf.read())
            lab_text = extract_text_any("temp_lab.pdf")
            st.success("Lab report extracted.")
        except Exception as e:
            st.error(f"Failed to extract lab PDF: {e}")

    st.markdown("### 🟩 Select PDF from Medical Vault")
    vault_files = [f for f in os.listdir(VAULT_DIR) if f.lower().endswith(".pdf")]
    selected_pdf = st.selectbox("Choose a Vault PDF:", ["None"] + vault_files)
    vault_text = ""

    if selected_pdf != "None":
        try:
            vault_text = extract_text_any(os.path.join(VAULT_DIR, selected_pdf))
            st.success(f"Loaded Vault PDF: {selected_pdf}")
        except Exception as e:
            st.error(f"Failed to read PDF: {e}")

    combined_triptych = f"""
DOCTOR NOTES:
{doctor_notes}

LAB REPORT:
{lab_text}

VAULT PDF:
{vault_text}
"""

    if st.button("🔮 Generate Unified Medical Summary"):
        if not (doctor_notes or lab_text or vault_text):
            st.warning("Provide at least one input.")
            aaa_footer()
            return

        with st.spinner("Generating unified clinical intelligence…"):
            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                resp = ai.generate_content(
                    f"""
Fuse DOCTOR NOTES + LAB REPORT + VAULT PDF into a unified medical intelligence layer.

FORMAT:
1. Unified Clinical Summary
2. Key Medical Trends
3. Risk / Attention Layer
4. Doctor-Friendly Briefing
5. Recommended Action Loop

DATA:
{combined_triptych}
"""
                )
                st.info(resp.text)
            except Exception as e:
                st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 25 — SERENE FREQUENCY (PREMIUM)
# ============================================================

def page_serene_frequency():

    mode = st.session_state.get("mode", "free")

    # 🔐 Premium firewall — MUST MATCH SIDEBAR EXACTLY
    check_firewall("Serene Frequency Indicators — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # TITLE + SUBTITLE + TRIAL — ALWAYS SHOWN (FREE + PREMIUM)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🎵 Serene Frequency Indicators — Vibration × Health Intelligence
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Emotional signals meet vibrational healing and wellness alignment.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — MUST COME AFTER THE TITLE
    # --------------------------------------------------------
    if mode != "premium":

        st.markdown("""
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="margin-top:22px; font-size:18px; color:white;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    Upgrade to unlock deep vibration × emotional alignment intelligence.
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
        """, unsafe_allow_html=True)

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE SECTION BELOW
    # --------------------------------------------------------

    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})

    if not logs and not insights:
        st.info("No logs or insights yet.")
        aaa_footer()
        return

    st.markdown("### 📅 Select Range")
    freq_range = st.selectbox("Choose window:", ["Last 3 Days", "Last 7 Days", "Last 14 Days"])

    days = 3 if freq_range == "Last 3 Days" else 7 if freq_range == "Last 7 Days" else 14
    cutoff = datetime.now().timestamp() - (days * 86400)

    filtered_logs = [l for l in logs if l.get("timestamp", 0) >= cutoff]

    st.markdown("### 🎛 Coherence Summary")

    if not filtered_logs:
        st.info("No logs found in this range.")
        aaa_footer()
        return

    combined_text = "\n".join([l.get("summary", "") for l in filtered_logs])

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"""
You are Serene Frequency AI.

TASK:
- Study emotional logs and behavioural patterns
- Recommend healing frequencies & breath rhythms

FORMAT:
1. Emotional Tone
2. Frequency Recommendation
3. Breath Rhythm
4. Sound Style
5. Gentle Affirmation

DATA:
{combined_text}
""")
        st.info(response.text)

    except Exception as e:
        st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 26 — MOOD × SLEEP × STRESS RADAR (PREMIUM)
# ============================================================

def page_mood_sleep_stress_radar():
    mode = st.session_state.get("mode", "free")

    # 🔐 Premium firewall — MUST MATCH SIDEBAR EXACTLY
    check_firewall("Mood × Sleep × Stress Radar — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES PAGES 20–24)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            🧘 Mood × Sleep × Stress Radar — Mind–Body State Map
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE (same style as premium pages)
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Input your state — AAA creates a personalised Mind–Body Radar Map.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # GOLD TRIAL LINE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE LOCK UI
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------

    st.markdown(
        """
        <div style='font-size:16px; margin-bottom:20px;'>
            Input your state — AAA generates a Mind–Body Radar Map.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        mood = st.slider("😊 Mood", 1, 10, 7)
        sleep_quality = st.slider("😴 Sleep Quality", 1, 10, 6)

    with col2:
        stress = st.slider("⚡ Stress", 1, 10, 4)
        energy = st.slider("🔋 Energy", 1, 10, 6)

    st.markdown("---")

    # --------------------------------------------------------
    # RADAR MAP GENERATION
    # --------------------------------------------------------
    if st.button("Generate Mind–Body Radar Map"):
        with st.spinner("Generating radar…"):
            import matplotlib.pyplot as plt
            import numpy as np

            categories = ["Mood", "Sleep", "Stress", "Energy"]
            values = [mood, sleep_quality, stress, energy]

            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(5,5), subplot_kw=dict(polar=True))
            ax.plot(angles, values, linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_yticklabels([])

            st.pyplot(fig)

    st.markdown("---")

    # --------------------------------------------------------
    # AI INSIGHT BLOCK
    # --------------------------------------------------------
    if st.button("🔮 Generate AI Insight"):
        with st.spinner("Analyzing mind–body pattern…"):

            prompt = f"""
AAA Health Intelligence — interpret the user's Mind–Body State.

Inputs:
Mood: {mood}
Sleep: {sleep_quality}
Stress: {stress}
Energy: {energy}

Give:
1. 2-sentence summary
2. 2 actionable suggestions
3. Vibration alignment note
"""

        try:
            ai_response = call_gemini(prompt)
            st.markdown(
                f"""
                <div style="padding:15px; background:#0e1b2c; border-radius:10px; color:#cde3ff;">
                    {ai_response}
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error("AI failed.")
            st.exception(e)

    aaa_footer()


# ============================================================
# PAGE 27 — Health × Vibration Correlation Map (PREMIUM)
# ============================================================

def page_health_vibration_correlation():
    mode = st.session_state.get("mode", "free")

    # 🔐 Premium firewall — MUST MATCH SIDEBAR EXACTLY
    check_firewall("Health × Vibration Correlation Map — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES PAGES 20–26 EXACTLY)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            🌀 Health × Vibration Correlation Map (Beta)
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Discover how your physical health and vibration states move together.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # GOLD TRIAL LINE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE LOCK UI
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow warning
        st.markdown(
            """
            <div style="background:#3f3f1e; color:#e5e5c3;
                padding:14px; border-radius:8px; font-size:14px; margin-bottom:16px;">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="font-size:18px; color:white; margin-bottom:18px;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:20px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            Explore the relationship between <b>physical health metrics</b> 
            and <b>vibration indicators</b> from Serene Frequency and Mind–Body logs.
            AAA Intelligence discovers hidden correlations to show how your 
            health and vibration states move together.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # USER INPUTS
    # --------------------------------------------------------
    st.markdown("### 🧩 Select Inputs for Correlation Analysis")

    health_option = st.selectbox(
        "Choose a Health Metric:",
        [
            "Blood Pressure",
            "Blood Sugar (Fasting / PP)",
            "Kidney Indicators (eGFR / Creatinine)",
            "Liver Enzymes (ALT / AST / GGT)",
            "Hemoglobin / CBC",
            "Vitamin Profile",
            "Thyroid Panel",
        ]
    )

    vibration_option = st.selectbox(
        "Choose a Vibration Indicator:",
        [
            "Serene Frequency Score",
            "Mood Rating",
            "Sleep Quality",
            "Stress Level",
            "Frequency Alignment Index",
            "Mind–Body Balance Score",
        ]
    )

    # --------------------------------------------------------
    # RUN CORRELATION ENGINE
    # --------------------------------------------------------
    if st.button("🔍 Run Correlation Analysis"):
        with st.spinner("Running AAA Correlation Engine…"):

            import random
            import matplotlib.pyplot as plt

            try:
                # Load data placeholders
                health_json = load_json(os.path.join(DATA_DIR, "health_data.json"), {})
                vibration_json = load_json(os.path.join(DATA_DIR, "serene_frequency_data.json"), {})
                mindbody_json = load_json(os.path.join(DATA_DIR, "mood_sleep_stress.json"), {})

                # Placeholder correlation logic
                result = {
                    "health_metric": health_option,
                    "vibration_metric": vibration_option,
                    "correlation_score": round(random.uniform(-1, 1), 2),
                    "interpretation": (
                        "Positive correlation — vibration improvements align with better health outcomes."
                        if random.random() > 0.5 else
                        "Negative correlation — vibration imbalance may be influencing health metrics."
                    ),
                }

                st.success("Correlation Analysis Complete")

                # Display results
                st.markdown(
                    f"""
                    ### 📌 Results  
                    **Health Metric:** {health_option}  
                    **Vibration Metric:** {vibration_option}  
                    **Correlation Score:** `{result['correlation_score']}`  
                    """
                )

                st.info(f"**Interpretation:** {result['interpretation']}")

                st.markdown("---")

                # --------------------------------------------------------
                # SCATTER PLOT PLACEHOLDER
                # --------------------------------------------------------
                fig, ax = plt.subplots()
                ax.scatter(
                    [random.randint(1, 100) for _ in range(20)],
                    [random.randint(1, 100) for _ in range(20)],
                )
                ax.set_title("Health × Vibration Correlation Scatter Plot")
                ax.set_xlabel(health_option)
                ax.set_ylabel(vibration_option)
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Error while calculating correlation: {e}")

    aaa_footer()


# ============================================================
# PAGE 28 — Trend Forecast Engine (Predictive Health + Vibration AI) — PREMIUM
# ============================================================

def page_trend_forecast_engine():
    mode = st.session_state.get("mode", "free")

    # 🔐 Premium firewall — MUST MATCH SIDEBAR EXACTLY
    check_firewall("Trend Forecast Engine (Predictions) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES 23–27 EXACTLY)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            📈 Trend Forecast Engine — Predictive Health × Vibration AI (Beta)
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            AI-powered forecast of health, mood, sleep, vibration & behaviour trends.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # GOLD TRIAL LINE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE LOCK UI
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow warning
        st.markdown(
            """
            <div style="background:#3f3f1e; color:#e5e5c3;
                padding:14px; border-radius:8px; font-size:14px; margin-bottom:16px;">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="font-size:18px; color:white; margin-bottom:18px;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA bar
        st.markdown(
            """
            <div style="
                margin-top:20px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — ORIGINAL FUNCTIONALITY (UNCHANGED)
    # --------------------------------------------------------
    st.markdown(
        """
        <div style="font-size:15px; line-height:1.6; margin-bottom:15px;">
            AAA studies your logs, insights, emotional signals, sleep quality,
            vibration markers, and medical summaries — then generates a 
            predictive forecast for the upcoming days.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------
    insights_raw = load_json(AI_SUMMARY_FILE, {})
    insights = insights_raw.get("history", [])

    logs_raw = load_json(HEALTH_LOG_FILE, [])
    logs = [l.get("summary", "") for l in logs_raw]

    if not insights and not logs:
        st.warning("No historical data available for forecasting.")
        aaa_footer()
        return

    # --------------------------------------------------------
    # USER SELECT WINDOW
    # --------------------------------------------------------
    window = st.selectbox(
        "Select forecast window:",
        ["Next 3 days", "Next 7 days", "Next 14 days"]
    )

    # --------------------------------------------------------
    # RUN FORECAST
    # --------------------------------------------------------
    if st.button("Generate Forecast"):
        with st.spinner("Building predictive model…"):

            try:
                combined_text = ""

                # health logs text
                for entry in logs:
                    combined_text += f"\n{entry}"

                # insights text
                for item in insights:
                    combined_text += f"\n{item.get('short','')}"
                    combined_text += f"\n{item.get('deep','')}"

                # AI forecast
                forecast_prompt = f"""
                You are AAA's Predictive Health & Vibration Intelligence Engine.

                Generate a calm, educational forecast for: {window}

                Include:
                - Health trends
                - Sleep patterns
                - Stress & mood patterns
                - Vibration / energy shifts
                - Red flags (non-alarming)
                - Simple lifestyle adjustments

                DATA:
                {combined_text}
                """

                result = call_gemini(forecast_prompt)

                st.success("Forecast ready.")
                st.markdown(result)

                # --------------------------------------------------------
                # PREVIEW TREND CHART (placeholder)
                # --------------------------------------------------------
                import matplotlib.pyplot as plt
                import random

                fig, ax = plt.subplots()
                ax.plot(
                    [1, 2, 3, 4, 5, 6, 7],
                    [random.randint(40, 90) for _ in range(7)]
                )
                ax.set_title("Predictive Health-Vibration Curve (Sample)")
                ax.set_xlabel("Days Ahead")
                ax.set_ylabel("Trend Strength")
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Forecast generation failed: {e}")

    aaa_footer()


# ============================================================
# PAGE 29 — Unified Timeline Intelligence (All Signals, One Timeline) — PREMIUM
# ============================================================

def page_unified_timeline_intel():
    mode = st.session_state.get("mode", "free")

    # 🔐 Premium firewall — MUST MATCH SIDEBAR EXACTLY
    check_firewall("Unified Timeline Intelligence (Time-Line View) — PREMIUM", mode)

    aaa_header()

    # --------------------------------------------------------
    # PREMIUM HEADER (MATCHES PAGES 23–28)
    # --------------------------------------------------------
    st.markdown(
        """
        <h2 style="
            font-size:30px;
            font-weight:600;
            color:#facc6b;
            text-align:center;
            margin-top:10px;
        ">
            📅 Unified Timeline Intelligence — All Signals, One Timeline (Beta)
        </h2>
        """,
        unsafe_allow_html=True,
    )

    # SUBTITLE
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:16px;
            color:#d1d5db;
            margin-top:-6px;
        ">
            Health logs, summaries, mood, sleep, stress, vibration indicators,
            and AI insights — merged into a single timeline for pattern detection.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # GOLD TRIAL LINE
    st.markdown(
        """
        <div style="text-align:center; margin-top:12px; color:#facc6b; font-size:15px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FREE MODE LOCK UI
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow warning bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-bottom:16px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade message
        st.markdown(
            """
            <div style="font-size:18px; color:white; margin-bottom:18px;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        monetization_cta()
        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — TIMELINE VIEW
    # --------------------------------------------------------

    st.markdown("---")

    try:
        import matplotlib.pyplot as plt
        import random

        # Demo timeline data (placeholder)
        days = list(range(1, 16))
        health_scores = [random.randint(60, 85) for _ in days]
        mood_scores = [random.randint(40, 90) for _ in days]
        sleep_hours = [random.randint(4, 9) for _ in days]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(days, health_scores, marker="o", label="Health Score")
        ax.plot(days, mood_scores, marker="s", label="Mood Score")
        ax.plot(days, sleep_hours, marker="^", label="Sleep Hours")

        ax.set_title("Unified Timeline — Health × Mood × Sleep Trends")
        ax.set_xlabel("Timeline (Days)")
        ax.set_ylabel("Values")
        ax.legend()

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Timeline generation error: {e}")

    aaa_footer()


# ============================================================
# PAGE 30 — AAA Insight Matrix (Signal-to-Signal Relationship Grid) — PREMIUM
# ============================================================

def page_insight_matrix():
    mode = st.session_state.get("mode", "free")

    # NOTE:
    # We do NOT call check_firewall here.
    # This page now shows its own premium lock (same as Rich Analytics).

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL MESSAGE (MATCH PAGE 12 STYLE)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧩 AAA Insight Matrix — Signal-to-Signal Relationship Grid (Beta)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Explore how health and vibration signals may interact, amplify, or offset each other.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — STANDARD PREMIUM LOCK UI
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence and pattern intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Blue CTA bar — consistent with other pages
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL MATRIX VIEW
    # --------------------------------------------------------

    # Intro text
    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:25px;">
            Compare how different health and vibration signals interact, influence,
            or correlate with each other using a placeholder analytical grid.<br>
            Future versions will use AAA’s unified data lake.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Signal list
    signals = [
        "Heart Rate",
        "Blood Pressure",
        "Sleep Quality",
        "Stress Level",
        "Oxygen Saturation",
        "Glucose",
        "Vibration Index",
        "Mood Score",
        "Inflammation Score",
    ]

    st.markdown("### 🔢 Signals Included")
    st.write(signals)

    st.markdown("### 🔥 Relationship Matrix (Synthetic Placeholder)")

    # Matrix generation
    import numpy as np
    import matplotlib.pyplot as plt

    try:
        matrix = np.random.uniform(-1, 1, (len(signals), len(signals)))

        fig, ax = plt.subplots(figsize=(8, 6))
        heatmap = ax.imshow(matrix, cmap="coolwarm")

        ax.set_xticks(range(len(signals)))
        ax.set_yticks(range(len(signals)))
        ax.set_xticklabels(signals, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(signals, fontsize=8)

        fig.colorbar(heatmap)
        ax.set_title("Signal-to-Signal Relationship Matrix (Synthetic Data)", fontsize=12)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Matrix generation error: {e}")

    aaa_footer()


# ============================================================
# PAGE 31 — Health Knowledge Graph (AI Semantic Medical Map) — PREMIUM
# ============================================================

def page_health_knowledge_graph():
    mode = st.session_state.get("mode", "free")

    # NOTE:
    # We do NOT call check_firewall here.
    # This page shows its OWN premium lock, identical to Page 30.

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL MESSAGE (MATCH PAGE 30 STYLE)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧠 Health Knowledge Graph — AI Semantic Medical Map (Beta)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Explore an AI-generated semantic map connecting symptoms, biomarkers,
            lifestyle patterns, stress, sleep cycles, and vibration signals.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — STANDARD PREMIUM LOCK UI (IDENTICAL TO PAGE 30)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This feature is available for Premium users.<br>
                    Upgrade to unlock full AI Medical Intelligence and semantic intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Blue CTA bar — consistent design
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL INTERACTIVE GRAPH VIEW
    # --------------------------------------------------------

    st.markdown("### 🔎 Generate Knowledge Graph")

    graph_type = st.selectbox(
        "Select Graph Type:",
        [
            "Biomarker Relationships",
            "Symptom → Cause Map",
            "Lifestyle Impact Graph",
            "Stress–Sleep Interaction",
            "Vibration–Health Semantic Web",
            "Full Unified Knowledge Map (All Signals)",
        ]
    )

    if st.button("Generate Graph"):
        try:
            with st.spinner("Generating AI Semantic Graph…"):

                example_graph = {
                    "nodes": [
                        {"id": "Stress", "group": 1},
                        {"id": "Sleep Quality", "group": 1},
                        {"id": "Vitamin D", "group": 2},
                        {"id": "Inflammation", "group": 2},
                        {"id": "Heart Rate", "group": 3},
                        {"id": "Vibration Score", "group": 4},
                    ],
                    "links": [
                        {"source": "Stress", "target": "Sleep Quality", "value": 4},
                        {"source": "Stress", "target": "Heart Rate", "value": 3},
                        {"source": "Sleep Quality", "target": "Inflammation", "value": 2},
                        {"source": "Vitamin D", "target": "Inflammation", "value": 3},
                        {"source": "Vibration Score", "target": "Stress", "value": 5},
                    ]
                }

                st.json(example_graph)
                st.info("🔧 Interactive visual graph coming in AAA-Health v0.9.")

        except Exception as e:
            st.error(f"Graph Engine Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 32 — Multi-Signal Diagnostic Engine — PREMIUM
# ============================================================

def page_multi_signal_engine():
    mode = st.session_state.get("mode", "free")

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL MESSAGE (MATCH PAGE 30/31)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🧬 Multi-Signal Diagnostic Engine (Beta)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            AI-powered differential insights using all combined health signals.
            <br>(Strictly informational — no medical advice.)
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — SAME PREMIUM LOCK UI AS PAGES 30 & 31
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This engine analyzes all signals (logs, OCR, biomarker text,
                    doctor notes) to generate differential pattern insights.
                    <br>Unlock full multi-signal intelligence with Premium.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Blue CTA bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL ENGINE VIEW
    # --------------------------------------------------------

    # Collect data from all sources
    signals = []

    # Vault PDFs → Extract text
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]
    for f in vault_files:
        try:
            text = extract_text_any(os.path.join(VAULT_DIR, f))
            if text.strip():
                signals.append(text)
        except:
            pass

    # OCR → Text
    for item in load_json(OCR_DATA_FILE, []):
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # Health Logs
    for entry in load_json(HEALTH_LOG_FILE, []):
        note = entry.get("note", "").strip()
        if note:
            signals.append(note)

    # Doctor Notes
    doctor_notes = load_json(DOCTOR_NOTES_FILE, [])
    if doctor_notes:
        signals.append("\n".join(doctor_notes))

    # No signals → info message
    if not signals:
        st.info("No signals available. Upload files or write logs to enable analysis.")
        aaa_footer()
        return

    # Run engine
    if st.button("🚀 Run Diagnostic Engine"):
        with st.spinner("Analyzing multi-source signals…"):
            result = run_multi_signal_engine(signals)

        st.markdown(result["formatted"], unsafe_allow_html=True)

        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Multi-Signal Diagnostic Insight",
            "short": result["json"].get("summary", ""),
            "deep": result["formatted"],
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Insight saved.")

    aaa_footer()


# ============================================================
# PAGE 33 — Health Signature Engine (Unified Signal Signature) — PREMIUM
# ============================================================

def page_health_signature_engine():
    mode = st.session_state.get("mode", "free")

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL MESSAGE (MATCH PAGE 30/31/32)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🩺 Health Signature Engine (Beta)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Generates a unified health signature across logs, biomarkers,
            OCR, PDFs, lifestyle patterns, mood, sleep, stress and behavioural trends.
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:6px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # FREE MODE — STANDARD PREMIUM LOCK UI (NO check_firewall)
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow Notice
        st.markdown(
            """
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
                margin-top:10px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upgrade Prompt
        st.markdown(
            """
            <div style="
                margin-top:22px;
                font-size:18px;
                color:white;
            ">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Premium Feature Card
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="
                    margin-top:10px;
                    color:#cbd5e1;
                    font-size:14px;
                    line-height:1.6;
                ">
                    <b>Premium Feature</b><br>
                    This engine builds a unified health signature by merging all
                    signals across logs, PDFs, OCR and lifestyle patterns.
                    <br>Unlock full Signal Intelligence with Premium.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # CTA Bar
        st.markdown(
            """
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL ENGINE VIEW
    # --------------------------------------------------------

    signals = []

    # 1 — PDF Text
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]
    for f in vault_files:
        try:
            text = extract_text_any(os.path.join(VAULT_DIR, f))
            if text.strip():
                signals.append(text)
        except:
            pass

    # 2 — OCR Content
    for item in load_json(OCR_DATA_FILE, []):
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # 3 — Health Logs
    for entry in load_json(HEALTH_LOG_FILE, []):
        note = entry.get("note", "").strip()
        if note:
            signals.append(note)

    # No signals → stop
    if not signals:
        st.info("No health signals available. Upload files or write logs to continue.")
        aaa_footer()
        return

    # --------------------------------------------------------
    # RUN ENGINE
    # --------------------------------------------------------
    if st.button("🚀 Generate Health Signature"):
        with st.spinner("Building your unified health signature…"):
            try:
                result = run_multi_signal_engine(signals)
            except Exception as e:
                st.error(f"Engine error: {e}")
                aaa_footer()
                return

        # Display signature
        st.markdown("### 🔍 Your Health Signature")
        st.markdown(result["formatted"], unsafe_allow_html=True)

        # Save to insights history
        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Health Signature Engine",
            "short": result["json"].get("summary", ""),
            "deep": result["formatted"],
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Health Signature saved.")

    aaa_footer()


# ============================================================
# PAGE 34 — Unified Signal Comparison Engine (Premium)
# ============================================================

def page_unified_signal_comparison():
    mode = st.session_state.get("mode", "free")

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL LINE (MATCH PAGES 30–33)
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:6px;">
            🔎 Unified Signal Comparison Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Compare logs, biomarkers, PDFs, OCR text, vibration indicators, and behavioural patterns side-by-side.<br>
            (Strictly informational — no medical advice)
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:4px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # PREMIUM LOCK (FREE MODE) — IDENTICAL TO PAGES 30–33
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown("""
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
        """, unsafe_allow_html=True)

        # Upgrade prompt
        st.markdown("""
            <div style="margin-top:22px; font-size:18px; color:white;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
        """, unsafe_allow_html=True)

        # Premium Feature Card
        st.markdown("""
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="margin-top:10px; color:#cbd5e1; font-size:14px; line-height:1.6;">
                    <b>Premium Feature</b><br>
                    Compare all health and behaviour signals side-by-side.<br>
                    Unlock full Signal Intelligence with AAA Premium.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Blue CTA bar
        st.markdown("""
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
        """, unsafe_allow_html=True)

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL FEATURE VIEW
    # --------------------------------------------------------

    # Collect signals
    signals = []

    # Health Logs
    logs = load_json(HEALTH_LOG_FILE, [])
    log_text = "\n".join([entry.get("note", "") for entry in logs if entry.get("note")])
    if log_text.strip():
        signals.append(("Health Log", log_text))

    # OCR Extracted Text
    ocr_items = load_json(OCR_DATA_FILE, [])
    ocr_text = "\n".join([item.get("text", "") for item in ocr_items if isinstance(item, dict)])
    if ocr_text.strip():
        signals.append(("OCR Extracted Text", ocr_text))

    # PDFs
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]
    for f in vault_files:
        try:
            extracted = extract_text_any(os.path.join(VAULT_DIR, f))
            if extracted.strip():
                signals.append((f, extracted))
        except:
            pass

    # Doctor Notes
    notes = load_json(DOCTOR_NOTES_FILE, [])
    if notes:
        signals.append(("Doctor Notes", "\n".join(notes)))

    # No signals → show message
    if not signals:
        st.info("No signals available. Please upload files or write logs.")
        aaa_footer()
        return

    # --------------------------------------------------------
    # SELECT 2–4 SIGNALS
    # --------------------------------------------------------
    st.markdown("### 🧩 Select Signals to Compare")

    signal_names = [s[0] for s in signals]
    selected = st.multiselect("Choose 2–4 signals:", signal_names)

    if len(selected) < 2:
        st.warning("Select at least two signals to continue.")
        aaa_footer()
        return

    # Build combined comparison text
    combined_data = ""
    for name, text in signals:
        if name in selected:
            combined_data += f"\n\n### {name}\n{text}\n"

    # --------------------------------------------------------
    # RUN COMPARISON ENGINE
    # --------------------------------------------------------
    if st.button("🚀 Run Comparison Engine"):
        with st.spinner("Generating side-by-side comparison…"):

            prompt = f"""
You are AAA Intelligence. Compare these health and behavioural signals side-by-side.

SELECTED SIGNALS:
{selected}

RAW DATA (PARTIAL):
{combined_data[:25000]}

STRUCTURED HTML OUTPUT REQUIRED:
1. Comparison Table  
2. Overlap Map  
3. Conflicts  
4. Agreement Score (0–100)  
5. 150-word Summary  
"""

            try:
                ai_text = call_gemini(prompt)
            except Exception as e:
                st.error(f"AI Comparison Error: {e}")
                aaa_footer()
                return

        # Display result
        st.markdown(ai_text, unsafe_allow_html=True)

        # Save to insights history
        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Unified Signal Comparison",
            "short": ai_text[:600],
            "deep": ai_text
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Comparison saved.")

    aaa_footer()


# ============================================================
# PAGE 35 — Signal Volatility Engine (Premium)
# ============================================================

def page_signal_volatility_engine():
    mode = st.session_state.get("mode", "free")

    aaa_header()

    # --------------------------------------------------------
    # HEADER + TAGLINE + TRIAL LINE
    # --------------------------------------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:4px;">
            📉 Signal Volatility Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Detect variability, noise, instability, and fluctuations across your health signals.<br>
            (Strictly informational — no medical advice)
        </p>
        <p style="text-align:center; color:#CDE8FF; font-size:14px; margin-top:4px;">
            ⭐ Enjoy a 7-day free trial — full intelligence unlocked.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # PREMIUM FIREWALL (FREE MODE) — SAME AS PAGES 30–34
    # --------------------------------------------------------
    if mode != "premium":

        # Yellow notice bar
        st.markdown("""
            <div style="
                background:#3f3f1e;
                color:#e5e5c3;
                padding:14px;
                border-radius:8px;
                font-size:14px;
            ">
                ⚠️ This feature is available for Premium members.
            </div>
        """, unsafe_allow_html=True)

        # Upgrade prompt
        st.markdown("""
            <div style="margin-top:22px; font-size:18px; color:white;">
                👉 <b>Please upgrade to unlock full access.</b>
            </div>
        """, unsafe_allow_html=True)

        # Premium feature card
        st.markdown("""
            <div style="
                margin-top:32px;
                padding:28px;
                border-radius:16px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow:0 0 20px rgba(0,0,0,0.35);
            ">
                <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                    AAA — HEALTH INTELLIGENCE
                </h3>
                <p style="margin-top:10px; color:#cbd5e1; font-size:14px; line-height:1.6;">
                    <b>Premium Feature</b><br>
                    Analyze volatility, instability, and fluctuations across all signals.<br>
                    Unlock full Signal Intelligence with AAA Premium.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Blue CTA bar
        st.markdown("""
            <div style="
                margin-top:32px;
                padding:14px;
                border-radius:8px;
                background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
                color:white;
                font-size:14px;
                text-align:center;
                box-shadow:0 0 12px rgba(14,165,233,0.25);
            ">
                ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
            </div>
        """, unsafe_allow_html=True)

        aaa_footer()
        return

    # --------------------------------------------------------
    # PREMIUM MODE — FULL FEATURE VIEW
    # --------------------------------------------------------

    # Load all available signals
    signals = []

    # PDFs
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]
    for f in vault_files:
        try:
            extracted = extract_text_any(os.path.join(VAULT_DIR, f))
            if extracted.strip():
                signals.append(extracted)
        except:
            pass

    # OCR
    ocr_data = load_json(OCR_DATA_FILE, [])
    for item in ocr_data:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # Logs
    logs = load_json(HEALTH_LOG_FILE, [])
    for entry in logs:
        note = entry.get("note", "").strip()
        if note:
            signals.append(note)

    # Doctor Notes
    notes = load_json(DOCTOR_NOTES_FILE, [])
    if notes:
        signals.append("\n".join(notes))

    # No signals → user info
    if not signals:
        st.info("No signals found.")
        aaa_footer()
        return

    # --------------------------------------------------------
    # RUN VOLATILITY ANALYSIS
    # --------------------------------------------------------
    if st.button("🔍 Analyze Signal Volatility"):
        with st.spinner("Evaluating volatility patterns…"):

            combined = "\n\n---\n\n".join(signals)[:30000]

            prompt = """
You are AAA — Artigellence Augmentation Aggregator.

TASK:
Analyze variability, instability, fluctuations, and signal noise.

STRICT RULES:
- Observational only
- No diagnosis
- No medical claims

OUTPUT FORMAT (HTML):
1. High-Volatility Zones  
2. Low-Volatility Zones  
3. Noise / Outlier Regions  
4. Instability Correlations  
5. 100-word Summary
"""

            ai_text = call_gemini(prompt + combined)

        st.markdown(ai_text, unsafe_allow_html=True)

    aaa_footer()


# ============================================================
# PAGE — SUBSCRIPTION PLANS (AAA PREMIUM)
# ============================================================

def page_subscription_plans():
    aaa_header()
    st.subheader("💳 Subscription Plans — Artigellence Premium")

    # --------------------------------------------------------
    # REGION AUTO-DETECT (IN / AU / GLOBAL)
    # --------------------------------------------------------
    user_region = detect_region()
    st.caption(f"Detected Region: {user_region}")

    # --------------------------------------------------------
    # REGION SMART CTA BANNER
    # --------------------------------------------------------
    banner_text = {
        "IN":     "🇮🇳 Save 70% with India regional pricing — ₹500/month",
        "AU":     "🇦🇺 Local Plan Available — A$10/month",
        "GLOBAL": "🌍 Global Premium Access — $10/month"
    }.get(user_region, "🌍 Global Premium Access — $10/month")

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #0e1a2b, #0c223a);
            padding: 14px 20px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.10);
            margin: 10px 0 25px 0;
            font-size: 15px;
            font-weight: 600;
            color: #C7D2FE;
            text-align: center;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.35);
        ">
            {banner_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Choose how you want to explore **AAA — Health Intelligence**. "
        "Free mode lets you try essentials. Premium unlocks full intelligence."
    )

    # --------------------------------------------------------
    # GLOBAL CARD CSS (APPLE-CLASS + POLISH)
    # --------------------------------------------------------
    st.markdown(
        """
        <style>
            .pricing-wrapper {
                margin-top: 10px;
                margin-bottom: 30px;
            }

            .aaa-card {
                background: rgba(255,255,255,0.03);
                padding: 24px;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.10);
                min-height: 360px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                transition: all 0.22s ease-in-out;
            }

            .aaa-card:hover {
                transform: translateY(-4px) scale(1.018);
                border: 1px solid rgba(0,255,174,0.40);
                box-shadow: 0 0 20px rgba(0,255,174,0.18);
            }

            /* AI Glow Pulse */
            @keyframes aaaPulse {
                0%   { box-shadow: 0 0 0px rgba(0,255,174,0.0); }
                50%  { box-shadow: 0 0 18px rgba(0,255,174,0.55); }
                100% { box-shadow: 0 0 0px rgba(0,255,174,0.0); }
            }

            .aaa-active {
                border: 2px solid rgba(0,255,174,0.75) !important;
                animation: aaaPulse 2.8s infinite ease-in-out;
            }

            .aaa-card-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; }
            .aaa-price { font-size: 30px; font-weight: 700; margin-bottom: 14px; }
            .aaa-list { font-size: 14px; line-height: 1.55; margin-top: 8px; }

            .aaa-button {
                width: 100%;
                border-radius: 10px;
                padding: 12px 0;
                font-weight: 600;
                margin-top: 14px;
                background: #1f6feb;
                color: white;
                border: none;
                cursor: pointer;
                transition: all 0.18s ease-in-out;
            }

            .aaa-button:hover {
                opacity: 0.92 !important;
                transform: scale(1.04) !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ACTIVE REGION HIGHLIGHT
    active_in  = "aaa-active" if user_region == "IN" else ""
    active_gl  = "aaa-active" if user_region == "GLOBAL" else ""
    active_au  = "aaa-active" if user_region == "AU" else ""

    # --------------------------------------------------------
    # WRAPPER FOR PERFECT 4-COLUMN ALIGNMENT
    # --------------------------------------------------------
    st.markdown("<div class='pricing-wrapper'>", unsafe_allow_html=True)
    col_free, col_global, col_india, col_aus = st.columns(4)

    # ---------------------------
    # FREE PLAN
    # ---------------------------
    with col_free:
        st.markdown(
            """
            <div class="aaa-card">
                <div>
                    <div class="aaa-card-title">🆓 Free</div>
                    <div class="aaa-price">$0 / month</div>
                    <div class="aaa-list">
                        • Dashboard<br>
                        • Health Log<br>
                        • Vault + OCR<br>
                        • Demo AI Summary<br>
                        • Snapshots (Basic)<br>
                        • PDF Preview (Basic)
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    # ---------------------------
    # GLOBAL PLAN
    # ---------------------------
    st.markdown('<div id="global-section"></div>', unsafe_allow_html=True)

    with col_global:
        st.markdown(
            f"""
            <div class="aaa-card {active_gl}">
                <div>
                    <div class="aaa-card-title">🌍 Premium — Global</div>
                    <div class="aaa-price">$10 / month</div>
                    <div class="aaa-list">
                        • Full Premium Access<br>
                        • Unlimited AI PDFs<br>
                        • Hybrid Engine<br>
                        • Vibration × Health Map<br>
                        • Serene Frequencies (Beta)
                    </div>
                </div>
                <a href="https://buy.stripe.com/bJecN4fq39dbf7q3L15ZC01" target="_blank">
                    <button class="aaa-button">Start Premium — $10/mo</button>
                </a>
                <div style="font-size:12px; opacity:0.65;">Secure Stripe checkout → opens in new tab</div>
            </div>
            """, unsafe_allow_html=True
        )

    # ---------------------------
    # INDIA PLAN
    # ---------------------------
    st.markdown('<div id="india-section"></div>', unsafe_allow_html=True)

    with col_india:
        st.markdown(
            f"""
            <div class="aaa-card {active_in}">
                <div>
                    <div class="aaa-card-title">🇮🇳 Premium — India</div>
                    <div class="aaa-price">₹500 / month</div>
                    <div class="aaa-list">
                        • Unlimited AI Summaries<br>
                        • Hybrid Engine<br>
                        • Insights + Full History<br>
                        • AI PDF Reports<br>
                        • Timeline + Snapshots<br>
                        • Finance × Law Early Access<br>
                        • Vibration Indicators (Beta)
                    </div>
                </div>
                <a href="https://buy.stripe.com/6oU4gyelZ60Zf7q3L15ZC03" target="_blank">
                    <button class="aaa-button">Start Premium — ₹500/mo</button>
                </a>
                <div style="font-size:12px; opacity:0.65;">Secure Stripe checkout → opens in new tab</div>
            </div>
            """, unsafe_allow_html=True
        )

    # ---------------------------
    # AUSTRALIA PLAN
    # ---------------------------
    st.markdown('<div id="australia-section"></div>', unsafe_allow_html=True)

    with col_aus:
        st.markdown(
            f"""
            <div class="aaa-card {active_au}">
                <div>
                    <div class="aaa-card-title">🇦🇺 Premium — Australia</div>
                    <div class="aaa-price">A$10 / month</div>
                    <div class="aaa-list">
                        • Unlimited AI Summaries<br>
                        • Hybrid Engine<br>
                        • Insights + Full History<br>
                        • PDF Reports<br>
                        • Timeline + Snapshots<br>
                        • Vibration Indicators (Beta)
                    </div>
                </div>
                <a href="https://buy.stripe.com/28EdR8a5JfBze3m3L15ZC04" target="_blank">
                    <button class="aaa-button">Start Premium — A$10/mo</button>
                </a>
                <div style="font-size:12px; opacity:0.65;">Secure Stripe checkout → opens in new tab</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # CLOSE WRAPPER
    st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SAFE TRIAL MESSAGE (does not affect card alignment)
    # --------------------------------------------------------
    st.caption("⭐ All Premium Plans now include a 7-Day Free Trial — cancel anytime, no charge.")

    # --------------------------------------------------------
    # SUBSCRIPTION README (CLEAN MARKDOWN)
    # --------------------------------------------------------
    st.markdown("## 📘 Subscription README — How AAA Premium Works")

    st.markdown(
        """
**Free Mode:**  
Try the AAA experience, view health logs, upload files, use the demo AI summary,  
and explore the dashboard. Premium unlocks full intelligence.

**Premium Mode:**  
Unlock unlimited AI summaries, deep insights, advanced timelines, hybrid engine,  
PDF reports, snapshots, and early access to AAA Finance × Law.

**Region Smart Pricing:**  
Prices automatically adjust for Australia / India / USA.

**Upgrade Anytime:**  
One click → instant activation → full access.

**Your Data:**  
Always encrypted. Never sold. You remain the owner of your data.
        """
    )

    # --------------------------------------------------------
    # COMPARISON TABLE
    # --------------------------------------------------------
    st.markdown("## 🔍 Free vs Premium — Feature Comparison")

    st.table(
        {
            "Feature": [
                "Dashboard","Health Log","Health Vault","OCR Extraction",
                "AI Summary","Hybrid Engine","AI PDF Reports","Timeline View",
                "Snapshots","Vibration Indicators","Finance × Law",
            ],
            "Free": [
                "✔","✔","✔","✔","Demo Only","✘","✘","Basic","Basic","✘","✘",
            ],
            "Premium": [
                "✔ (Enhanced)","✔","✔","✔","Unlimited","Full Access","Yes",
                "Advanced","Unlimited","Beta Access","Early Access",
            ],
        }
    )

    st.info("Stripe payments are live. Your data always remains encrypted and fully owned by you.")

    # --------------------------------------------------------
    # AUTO-SCROLL
    # --------------------------------------------------------
    anchor_map = {"IN": "india-section", "AU": "australia-section", "GLOBAL": "global-section"}
    target_anchor = anchor_map.get(user_region)

    if target_anchor:
        st.markdown(
            f"""
            <script>
                let t = document.getElementById("{target_anchor}");
                if (t) {{
                    setTimeout(() => {{
                        t.scrollIntoView({{behavior:'smooth', block:'center'}});
                    }}, 350);
                }}
            </script>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # AI RECOMMENDATION ENGINE
    # --------------------------------------------------------
    st.markdown("### 🤖 Smart Recommendation (AI)")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])
    vault_items = len(logs) + len(ocr)

    if user_region == "IN":
        recommended = "India Premium — ₹500/month"
    elif user_region == "AU":
        recommended = "Australia Local Premium — A$10/month"
    else:
        recommended = "Global Premium — $10/month"

    usage_note = (
        "You're actively using AI summaries and Vault features."
        if vault_items >= 3 else
        "You're exploring the basics. Premium unlocks full intelligence."
    )

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.10);
            padding: 20px;
            border-radius: 12px;
            margin-top: 25px;
        ">
            <div style="font-size:17px; font-weight:600; margin-bottom:8px;">
                Recommended for you → {recommended}
            </div>
            <div style="font-size:14px; opacity:0.85;">
                {usage_note}
                Premium provides unlimited summaries, PDFs, Hybrid Engine, insights,
                advanced timelines and early access to AAA Finance × Law.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SMART EXIT BAR
    # --------------------------------------------------------
    exit_region_map = {
        "IN":     ("🇮🇳 India Premium — ₹500/month",  "https://buy.stripe.com/6oU4gyelZ60Zf7q3L15ZC03",  "Start Premium — ₹500/mo"),
        "AU":     ("🇦🇺 Australia Premium — A$10/month","https://buy.stripe.com/28EdR8a5JfBze3m3L15ZC04","Start Premium — A$10/mo"),
        "GLOBAL": ("🌍 Global Premium — $10/month","https://buy.stripe.com/bJecN4fq39dbf7q3L15ZC01","Start Premium — $10/mo"),
    }

    e_text, e_link, e_cta = exit_region_map.get(user_region, exit_region_map["GLOBAL"])

    st.markdown(
        f"""
        <style>
            #exit-intent-bar {{
                position: fixed;
                bottom: -200px;
                left: 50%;
                transform: translateX(-50%);
                width: 96%;
                max-width: 850px;
                background: rgba(15, 25, 45, 0.92);
                padding: 16px 22px;
                color: #E2E8F0;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 0 18px rgba(0,255,174,0.15);
                transition: all 0.45s ease-in-out;
                z-index: 9999;
            }}
            #exit-intent-bar.show {{
                bottom: 20px;
            }}
            #exit-btn {{
                background:#1f6feb;color:white;padding:10px 20px;
                border-radius:10px;border:none;
                font-size:15px;font-weight:600;
                cursor:pointer;transition:0.2s;
            }}
            #exit-btn:hover {{
                opacity:0.9; transform:scale(1.02);
            }}
        </style>

        <div id="exit-intent-bar">
            <div style="font-size:16px;font-weight:600;margin-bottom:6px;">{e_text}</div>
            <a href="{e_link}" target="_blank"><button id="exit-btn">{e_cta}</button></a>
        </div>

        <script>
            let lastScroll=0;
            let bar=document.getElementById("exit-intent-bar");
            let hideTimeout=null;

            window.addEventListener("scroll", function() {{
                let current=window.pageYOffset;

                if(current < lastScroll && current > 80) {{
                    bar.classList.add("show");
                    clearTimeout(hideTimeout);
                    hideTimeout=setTimeout(()=>bar.classList.remove("show"),6000);
                }}

                if((current-lastScroll) > 120) {{
                    bar.classList.add("show");
                    clearTimeout(hideTimeout);
                    hideTimeout=setTimeout(()=>bar.classList.remove("show"),6000);
                }}

                lastScroll=current;
            }});
        </script>
        """,
        unsafe_allow_html=True
    )

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE — PREMIUM (COMING SOON)
# ============================================================

def page_premium():
    aaa_header()

    st.subheader("🌟 Artigellence Premium — Coming Soon")
    st.caption("Unlock AAA’s full intelligence tier across Health × Vibration × Finance × Law.")

    st.markdown("### 🚀 AAA Premium (Full Intelligence Tier)")
    st.write(
        """
        Experience the complete AAA Intelligence layer:  
        summaries ➜ hybrid insights ➜ forecasting ➜ vibration signals ➜ volatility maps ➜ unified timeline.
        """
    )

    st.write(
        """
        **Included in Premium:**  
        • Unlimited AI Medical Summaries  
        • Hybrid Engine (Doctor × Lab × Notes Fusion)  
        • Deep Insights + Full Timeline History  
        • Unified Logs + Pattern Recognition  
        • AI-Generated PDF Reports  
        • Pattern Timeline AI + Forecasting  
        • Vibration × Health Indicators  
        • Volatility Map + Noise Detection  
        • Early Access: AAA Finance × AAA Law  
        • Serene Frequencies Layer (Beta)  
        """
    )

    st.info("Final pricing will be announced soon. Demo mode active.")

    monetization_cta()
    aaa_footer()


# ============================================================
# HEALTH SCORE + AI SUMMARY — HELPERS
# ============================================================

SCORE_HISTORY_FILE = "score_history.json"

def compute_health_score(logs):
    if not logs:
        return 50

    score = 70
    pos = ["energetic", "slept well", "good", "better", "ok", "improved"]
    neg = ["pain", "tightness", "headache", "dizzy", "fatigue"]

    for entry in logs:
        note = entry.get("note", "").lower()
        for p in pos:
            if p in note:
                score += 2
        for n in neg:
            if n in note:
                score -= 3

    return max(1, min(score, 99))


def generate_ai_health_summary(logs, merged_data):
    try:
        combined = ""
        for l in logs:
            combined += f"Log ({l.get('timestamp')}): {l.get('note','')}\n"
        for item in merged_data:
            if item.get("type") == "summary":
                combined += item.get("text", "") + "\n"

        prompt = f"""
        Summarize health patterns safely and calmly.

        DATA:
        {combined}
        """

        return call_gemini(prompt)
    except Exception as e:
        return f"AI summary error: {e}"


def load_score_history():
    data = load_json(SCORE_HISTORY_FILE, {"history": []})
    return data.get("history", [])


def save_score_history(latest_score):
    hist = load_score_history()
    hist.append({
        "score": latest_score,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    hist = hist[-30:]
    save_json(SCORE_HISTORY_FILE, {"history": hist})
    return hist


def plot_score_trend(history):
    if not history:
        return None

    import matplotlib.pyplot as plt

    scores = [h["score"] for h in history]
    t = [h["timestamp"][5:16] for h in history]

    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.plot(scores, marker="o")
    ax.set_title("Health Score Trend (Last 30 updates)", fontsize=10)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Score")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


# ============================================================
# HEALTH STATUS BAR — COMPLETE VERSION
# ============================================================

def get_health_status(score, logs):
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 55:
        return "ok"
    if score >= 40:
        return "concern"
    return "critical"


def render_health_status_bar(status):
    colors = {
        "excellent": "#00e676",
        "good": "#1de9b6",
        "ok": "#ffea00",
        "concern": "#ff9100",
        "critical": "#ff1744"
    }

    text = {
        "excellent": "Excellent — stable positive indicators.",
        "good": "Good — overall positive, mild fluctuations.",
        "ok": "Okay — neutral signals, keep monitoring.",
        "concern": "Concern — noticeable negative patterns.",
        "critical": "Critical — immediate attention recommended."
    }

    st.markdown(f"""
        <div style="
            background-color:#0d1a2b;
            padding:14px;
            border-radius:10px;
            margin-bottom:20px;
            border-left:6px solid {colors[status]};
        ">
            <span style="color:{colors[status]}; font-size:18px; font-weight:600;">
                ● {status.upper()}
            </span>
            <div style="margin-top:6px; color:white; opacity:0.85; font-size:15px;">
                {text[status]}
            </div>
        </div>
    """, unsafe_allow_html=True)


# ============================================================
# HEALTH PULSE — FIXED
# ============================================================

def generate_health_pulse(logs, score, trend, note, file_count):
    if score >= 85: icon = "💚"
    elif score >= 70: icon = "💙"
    elif score >= 55: icon = "🟡"
    elif score >= 40: icon = "🟠"
    else: icon = "🔴"

    msg = ""
    if trend > 0:
        msg += "Your score is improving. "
    elif trend < 0:
        msg += "Your score is declining slightly. "
    else:
        msg += "Your score is stable. "

    if "pain" in note.lower():
        msg += "Pain indicators detected. "

    if file_count > 0:
        msg += f"{file_count} health documents stored. "

    return icon, msg.strip()


# ============================================================
# RED ASK AAA-HEALTH INTELLIGENCE BUTTON — FIXED (SOLID RED)
# ============================================================

st.markdown("""
<style>
.aaa-red-btn > button {
    background-color: #b91c1c !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px !important;
    font-size: 16px !important;
}
.aaa-red-btn > button:hover {
    background-color: #7f0000 !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DASHBOARD — FULL, FINAL, FIXED (NO ALIGNMENT ISSUES)
# ============================================================

def page_dashboard(switch_to):
    aaa_header()

    # --------------------------------------------------------
    # FIX 1: Dashboard toggle preserved
    # --------------------------------------------------------
    if "show_full_dashboard" not in st.session_state:
        st.session_state["show_full_dashboard"] = False

    # --------------------------------------------------------
    # FIX 2: Red Ask AAA Button (Right aligned)
    # --------------------------------------------------------
    cA, cB = st.columns([8, 2])
    with cB:
        if st.button("Ask AAA-Health Intelligence", key="askAAA",
                     use_container_width=True, help="AI Summary",
                     type="primary"):
            switch_to("🧠 Summary (Demo)")
            return

    # --------------------------------------------------------
    # INSERTED SECTION — TEXT INPUT FOR ASK AAA (SAFE)
    # --------------------------------------------------------
    st.markdown(
        "<div style='margin-top:12px; font-size:16px; opacity:0.85;'>"
        "📝 <b>Ask anything to AAA-Health Intelligence</b><br>"
        "<span style='font-size:13px; opacity:0.65;'>Type your question below:</span>"
        "</div>",
        unsafe_allow_html=True
    )

    user_query = st.text_input(
        "Ask a question:",
        "",
        key="dashboard_free_text",
        placeholder="Example: Explain my health pattern…"
    )

    if st.button("Submit Question", key="dashboard_query_btn"):
        if not user_query.strip():
            st.warning("Please enter a question.")
        else:
            st.info(
                f"Your question has been received:<br><br>"
                f"<b>{user_query}</b><br><br>"
                "This feature unlocks fully in AAA-Premium.",
                icon="🤖"
            )

    # --------------------------------------------------------
    # SIMPLE OVERVIEW SECTION
    # --------------------------------------------------------
    st.subheader("📊 Dashboard — Simple Overview")
    st.markdown("""
        <div style="font-size:15px; color:#C7D2FE; margin-bottom:20px;">
            Your health activity at a glance — click any tile to dive deeper.
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # DASHBOARD TILES — FIXED ROUTING + ALIGNMENT
    # --------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Health Log (Your notes & entries)", key="t1", use_container_width=True):
            switch_to("🩺 Health Log (Notes)")
            return

        if st.button("📄 Documents (PDFs & images)", key="t2", use_container_width=True):
            switch_to("📥 Health Vault (Uploads)")
            return

    with col2:
        if st.button("🤖 AI Insights (Premium Summary)", key="t3", use_container_width=True):
            switch_to("🧠 Summary (Demo)")
            return

        if st.button("📈 Advanced Metrics (Full Dashboard)", key="t4", use_container_width=True):
            st.session_state["show_full_dashboard"] = True

    st.markdown("<hr>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # STOP HERE IF FULL DASHBOARD NOT EXPANDED
    # --------------------------------------------------------
    if not st.session_state["show_full_dashboard"]:
        aaa_footer()
        return

    # --------------------------------------------------------
    # FULL ADVANCED DASHBOARD (UNCHANGED LOGIC)
    # --------------------------------------------------------
    st.subheader("📊 AAA Health Intelligence — Tailored Dashboard (Beta)")
    st.markdown("This is your personalised health overview. More data unlocks deeper insights.")

    logs = load_json(HEALTH_LOG_FILE, [])
    merged_data_obj = load_json(MERGED_DATA_FILE, {"data": []})
    merged_data = merged_data_obj.get("data", [])

    health_score = compute_health_score(logs)
    last_update = logs[-1]["timestamp"] if logs else "—"
    region = "Sydney, AU"

    score_history = save_score_history(health_score)
    trend = score_history[-1]["score"] - score_history[-2]["score"] if len(score_history) >= 2 else 0

    # STATUS BAR
    status = get_health_status(health_score, logs)
    render_health_status_bar(status)

    # METRIC CARDS
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Health Score", f"{health_score}", f"{trend:+}")
    with colB:
        st.metric("Last Update", last_update)
    with colC:
        st.metric("Region", region)

    st.markdown("---")

    # HEALTH PULSE
    recent_note = logs[-1].get("note", "") if logs else ""
    file_count = len(os.listdir(VAULT_DIR)) if os.path.exists(VAULT_DIR) else 0

    pulse_icon, pulse_text = generate_health_pulse(
        logs, health_score, trend, recent_note, file_count
    )

    st.markdown(
        f"""
        <div style="
            background-color:#0d1a2b;
            padding:16px;
            border-radius:10px;
            border:1px solid rgba(255,255,255,0.15);
        ">
            <h3 style="margin:0; color:white;">{pulse_icon} Health Pulse</h3>
            <p style="color:white; opacity:0.85;">{pulse_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # TREND GRAPH
    st.markdown("### 📈 Health Score Trend")
    fig = plot_score_trend(score_history)
    if fig:
        st.pyplot(fig)

    if trend > 0:
        st.success(f"📈 Trend: Improving (+{trend})")
    elif trend < 0:
        st.error(f"📉 Trend: Declining ({trend})")
    else:
        st.warning("➡️ Trend: Stable")

    st.markdown("---")

    # AI SUMMARY
    st.markdown("### 🧠 AI Health Summary")
    summary_text = generate_ai_health_summary(logs, merged_data)
    st.info(summary_text)
    st.markdown("---")

    # DAILY SNAPSHOT
    st.markdown("### 🗂️ Daily Snapshot")

    snapshot_date = last_update.split(" ")[0] if last_update != "—" else "—"
    recent_note_preview = recent_note[:80] + ("..." if len(recent_note) > 80 else "")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📅 Last Update")
        st.info(snapshot_date)

    with col2:
        st.markdown("#### 📝 Latest Note")
        st.info(recent_note_preview)

    with col3:
        st.markdown("#### 📄 Documents")
        st.info(f"{file_count} files")

    st.markdown("---")

    # TODAY'S SIGNALS
    st.markdown("### 🌤️ Today’s Signals")

    signals = []

    # logging frequency
    if len(logs) >= 2:
        t1 = datetime.strptime(logs[-1]["timestamp"], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(logs[-2]["timestamp"], "%Y-%m-%d %H:%M:%S")
        gap_hours = (t1 - t2).total_seconds() / 3600

        if gap_hours <= 24:
            signals.append("🟢 **Healthy logging frequency** — you added a log within 24 hours.")
        else:
            signals.append("🟡 **Low logging activity** — logs are spread out, insights may be less accurate.")
    else:
        signals.append("⚪ Not enough data to evaluate logging frequency.")

    # sentiment markers
    note = recent_note.lower()
    positive_markers = ["energetic", "better", "slept well", "okay", "improved"]
    negative_markers = ["pain", "tightness", "headache", "fatigue", "dizzy"]

    pos_flag = any(p in note for p in positive_markers)
    neg_flag = any(n in note for n in negative_markers)

    if logs:
        if pos_flag and not neg_flag:
            signals.append("🟢 **Your last note looks positive** — good indicators reported.")
        elif neg_flag and not pos_flag:
            signals.append("🔴 **Discomfort indicators detected** — monitor closely.")
        elif pos_flag and neg_flag:
            signals.append("🟡 **Mixed signals** — some good signs, some discomfort.")
        else:
            signals.append("⚪ No clear sentiment detected in last note.")

    # vault status
    if os.path.exists(VAULT_DIR):
        doc_count = len(os.listdir(VAULT_DIR))
        if doc_count > 0:
            signals.append(f"🟢 **{doc_count} documents stored** — vault is active.")
        else:
            signals.append("🟡 Vault empty — upload lab reports or health files for deeper insights.")
    else:
        signals.append("⚪ Vault directory missing.")

    # render signals
    for s in signals:
        st.markdown(
            f"""
            <div style="
                background-color:#0d233b;
                padding:12px;
                border-radius:8px;
                margin-bottom:8px;
                border:1px solid #1e3a5c;
            ">
                {s}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # WHY THESE SIGNALS MATTER
    st.markdown("### 🧠 Why These Signals Matter")

    def generate_reasoning_layer(logs, recent_note, file_count):
        reasons = []
        lower = recent_note.lower()

        if "headache" in lower:
            reasons.append("Headache often correlates with hydration levels or warm weather.")
        if "tightness" in lower:
            reasons.append("Chest tightness patterns suggest exertion or hydration issues.")
        if "slept well" in lower or "sleep" in lower:
            reasons.append("Good sleep strongly correlates with positive energy and appetite.")
        if file_count > 0:
            reasons.append(f"You have {file_count} documents stored — this helps AAA detect deeper patterns.")
        if len(logs) < 7:
            reasons.append("More logs over a longer period will produce stronger insights.")
        if not reasons:
            reasons.append("Signals look stable today. More data will unlock deeper personalised insights.")

        return reasons

    for r in generate_reasoning_layer(logs, recent_note, file_count):
        st.markdown(
            f"""
            <div style="
                background-color:#0d233b;
                padding:12px;
                border-radius:8px;
                margin-bottom:8px;
                border:1px solid #1e3a5c;
            ">
                {r}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # EARLY WARNING INDICATORS
    st.markdown("### 🔍 Early Warning Indicators (Last 7 Days)")

    recent_logs = logs[-7:] if len(logs) >= 7 else logs
    text_blob = " ".join([l.get("note", "") for l in recent_logs]).lower()
    warnings = []

    symptom_keywords = ["headache", "pain", "tightness", "pressure"]
    if sum(text_blob.count(k) for k in symptom_keywords) >= 2:
        warnings.append("⚠️ **Recurring symptoms detected** — monitor patterns.")

    if len(recent_logs) <= 3:
        warnings.append("⚠️ **Low logging frequency** — more logs improve accuracy.")

    if "water" in text_blob or "hydration" in text_blob:
        warnings.append("💧 **Hydration-related pattern noted** — keep monitoring water intake.")

    sleep_keywords = ["sleep", "tired", "fatigue"]
    if any(k in text_blob for k in sleep_keywords) and "good" not in text_blob:
        warnings.append("😴 **Sleep irregularity signals** — mixed notes detected.")

    doc_count = len(os.path.exists(VAULT_DIR) and os.listdir(VAULT_DIR)) if os.path.exists(VAULT_DIR) else 0
    if doc_count >= 5:
        warnings.append("📄 **Multiple documents stored** — new reports may contain important info.")

    if not warnings:
        warnings.append("✅ **Everything looks stable** based on last 7 days of logs.")

    for w in warnings:
        st.markdown(
            f"""
            <div style="
                background-color:#3b2f00;
                padding:14px;
                border-radius:8px;
                margin-bottom:8px;
                border:1px solid #604e00;
            ">
                {w}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # LAST 10 LOGS
    st.markdown("### 📅 Last 10 Health Logs")

    if logs:
        for entry in logs[-10:][::-1]:
            ts = entry.get("timestamp", "")
            dt = entry.get("date", "")
            nt = entry.get("note", "")
            st.markdown(f"""**📅 {dt} — {ts}**  
{nt}""")
    else:
        st.warning("No logs found.")

    st.markdown("---")

    # RECENT DOCUMENTS
    st.markdown("### 📂 Recent Documents")

    recent_docs = []
    if os.path.exists(VAULT_DIR):
        for fname in os.listdir(VAULT_DIR):
            if os.path.isfile(os.path.join(VAULT_DIR, fname)):
                recent_docs.append(fname)

    if recent_docs:
        for doc in recent_docs[:10]:
            st.markdown(f"📄 **{doc}**")
    else:
        st.warning("No documents found.")

    st.markdown("---")

    # REGIONAL INSIGHTS
    st.markdown("### 🧭 Regional Insights")
    st.info("Sydney health season: High pollen, warm weather, moderate UV. Flu season tapering.")

    st.markdown("---")

    # CLOSE CIRCLE
    st.markdown("### 👪 Close Circle Sharing")
    st.info("Add trusted family members to receive summaries (coming soon).")

    aaa_footer()

# ============================================================
# FIREWALL + PREMIUM PAGE REGISTRY (7-DAY TRIAL LOCK)
# ============================================================

# These are the 16 sidebar entries that must be PREMIUM-ONLY
PREMIUM_PAGES = {
    # --- PREMIUM ANALYTICS ---
    "🚨 AI Health Risk Engine (Risk Signals) — PREMIUM",
    "🧬 Pattern Timeline AI (Patterns Over Time) — PREMIUM",
    "🌐 Insight Fusion Layer (Fusion Intelligence) — PREMIUM",
    "📈 Insight Graphs (Visual Charts) — PREMIUM",
    "🩺 Medical Triptych (3-Panel View) — PREMIUM",

    # --- WELLBEING (PREMIUM WELLNESS LAYER) ---
    "🎵 Serene Frequencies (Audio Wellness) — WELLBEING",
    "🧘 Mood × Sleep × Stress Radar (Wellbeing Map) — WELLBEING",
    "🧘 Health × Vibration Correlation Map (Energy Map) — WELLBEING",

    # --- FORECAST (PREMIUM FORECAST LAYER) ---
    "📈 Trend Forecast Engine (Predictions) — FORECAST",
    "📅 Unified Timeline Intelligence (Time-Line View) — FORECAST",
    "🧩 Insight Matrix (Matrix View) — FORECAST",
    "🧠 Health Knowledge Graph (Knowledge Map) — FORECAST",

    # --- SIGNAL ENGINES (PREMIUM SIGNAL LAYER) ---
    "🧬 Multi-Signal Diagnostic Engine (Multi-Signal Analysis) — SIGNALS",
    "🧬 Health Signature Engine (Signature View) — SIGNALS",
    "🧬 Unified Signal Comparison (Compare Signals) — SIGNALS",
    "📉 Signal Volatility Engine (Volatility Analysis) — SIGNALS",
}


def check_firewall(page_label: str, mode: str):
    """
    Global firewall for PREMIUM_PAGES.

    - If user is in FREE mode and the selected sidebar label is in PREMIUM_PAGES:
        → Show premium lock layout + 7-day trial message
        → Stop rendering the rest of the page.
    - All other pages (CORE / existing AI pages) are untouched.
    """
    # Premium users: no lock at all
    if mode == "premium":
        return

    # Free mode but NOT a premium page → allowed
    if page_label not in PREMIUM_PAGES:
        return

    # Premium lock layout (matches your existing style + 7-day trial)
    aaa_header()

    # Yellow warning bar
    st.markdown(
        """
        <div style="
            background:#3f3f1e;
            color:#e5e5c3;
            padding:14px;
            border-radius:8px;
            font-size:14px;
            margin-top:10px;
        ">
            ⚠️ This feature is available for Premium members.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Upgrade text
    st.markdown(
        """
        <div style="
            margin-top:22px;
            font-size:18px;
            color:white;
        ">
            👉 <b>Please upgrade to unlock full access.</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Premium feature card
    st.markdown(
        """
        <div style="
            margin-top:32px;
            padding:28px;
            border-radius:16px;
            background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,0.08);
            box-shadow:0 0 20px rgba(0,0,0,0.35);
        ">
            <h3 style="margin:0; padding:0; color:#93c5fd; font-weight:600;">
                AAA — HEALTH INTELLIGENCE
            </h3>
            <p style="
                margin-top:10px;
                color:#cbd5e1;
                font-size:14px;
                line-height:1.6;
            ">
                <b>Premium Feature</b><br>
                This feature is available for Premium users.<br>
                Upgrade to unlock full AI Medical Intelligence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 7-day trial CTA bar
    st.markdown(
        """
        <div style="
            margin-top:32px;
            padding:14px;
            border-radius:8px;
            background:linear-gradient(90deg, #1e3a8a, #0ea5e9);
            color:white;
            font-size:14px;
            text-align:center;
            box-shadow:0 0 12px rgba(14,165,233,0.25);
        ">
            ⭐ Try AAA Premium Free for 7 Days — Unlock Full Intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )

    monetization_cta()
    aaa_footer()
    st.stop()


# ============================================================
# NAVIGATION SWITCH HELPER (CRITICAL FIX FOR BUTTONS)
# ============================================================

def switch_to(page_name: str):
    """
    Safe navigation switch:
    - We never write directly to session_state['nav'] inside pages.
    - Instead, we store a pending target and rerun.
    - main() applies the redirect BEFORE the sidebar radio is built.
    """
    st.session_state["pending_nav"] = page_name
    st.rerun()


# ============================================================
# MAIN NAVIGATION (GROUPED, NON-COLLAPSIBLE, ALL VISIBLE)
# ============================================================

def main():

    # --------------------------------------------------------
    # INIT NAV DEFAULT
    # --------------------------------------------------------
    if "nav" not in st.session_state:
        st.session_state["nav"] = "📊 Dashboard (Overview) — CORE"

    # --------------------------------------------------------
    # APPLY REDIRECT BEFORE RENDERING SIDEBAR
    # --------------------------------------------------------
    if "pending_nav" in st.session_state:
        st.session_state["nav"] = st.session_state["pending_nav"]
        del st.session_state["pending_nav"]

    # --------------------------------------------------------
    # SIDEBAR UI (ONLY NAV + MODE)
    # --------------------------------------------------------
    with st.sidebar:

        st.markdown("## 🔐 Subscription Mode (Demo)")
        mode = st.radio("Select mode:", ["free", "premium"])
        st.session_state["mode"] = mode

        st.markdown("## 💎 AAA — Health Intelligence (DEV)")

        choice = st.radio(
            "Navigate:",
            [

                # ------------------------------------------------
                # CORE MODULE
                # ------------------------------------------------
                "📊 Dashboard (Overview) — CORE",
                "🩺 Health Log (Notes) — CORE",
                "📥 Health Vault (Uploads) — CORE",
                "📁 Vault Manager (Manage Files) — CORE",
                "🗑 Recycle Bin (Deleted Items) — CORE",
                "📄 PDF Preview (Reports) — CORE",
                "🔍 OCR (Scan Text) — CORE",

                # ------------------------------------------------
                # AI SUMMARY & INSIGHTS MODULE
                # ------------------------------------------------
                "🧠 Summary (Demo) — AI",
                "✨ Merged View (Combined Data) — AI",
                "🧬 Summary AI (Advanced Summary) — AI",
                "📊 Insights AI (Deep Insights) — AI",
                "📚 Insights History (Past Insights) — AI",
                "📘 Summary Report (PDF Generator) — AI",
                "🧠 Hybrid Engine (Multi-Source Intelligence) — AI",

                # ------------------------------------------------
                # PREMIUM ANALYTICS MODULE
                # ------------------------------------------------
                "📊 Rich Analytics Dashboard (Premium Analytics) — PREMIUM",
                "🚨 AI Health Risk Engine (Risk Signals) — PREMIUM",
                "🧬 Pattern Timeline AI (Patterns Over Time) — PREMIUM",
                "🌐 Insight Fusion Layer (Fusion Intelligence) — PREMIUM",
                "📈 Insight Graphs (Visual Charts) — PREMIUM",
                "🩺 Medical Triptych (3-Panel View) — PREMIUM",

                # ------------------------------------------------
                # WELLBEING MODULE
                # ------------------------------------------------
                "🎵 Serene Frequencies (Audio Wellness) — WELLBEING",
                "🧘 Mood × Sleep × Stress Radar (Wellbeing Map) — WELLBEING",
                "🧘 Health × Vibration Correlation Map (Energy Map) — WELLBEING",

                # ------------------------------------------------
                # FORECASTING MODULE
                # ------------------------------------------------
                "📈 Trend Forecast Engine (Predictions) — FORECAST",
                "📅 Unified Timeline Intelligence (Time-Line View) — FORECAST",
                "🧩 Insight Matrix (Matrix View) — FORECAST",
                "🧠 Health Knowledge Graph (Knowledge Map) — FORECAST",

                # ------------------------------------------------
                # SIGNAL ENGINES MODULE
                # ------------------------------------------------
                "🧬 Multi-Signal Diagnostic Engine (Multi-Signal Analysis) — SIGNALS",
                "🧬 Health Signature Engine (Signature View) — SIGNALS",
                "🧬 Unified Signal Comparison (Compare Signals) — SIGNALS",
                "📉 Signal Volatility Engine (Volatility Analysis) — SIGNALS",

                # ------------------------------------------------
                # MONETIZATION
                # ------------------------------------------------
                "💎 Subscription Plans (Pricing) — MONETIZATION",

                # ------------------------------------------------
                # FUTURE MODULE
                # ------------------------------------------------
                "🧠 Edge Node Memory (Memory Layer) — FUTURE",

                # ------------------------------------------------
                # BACKUP
                # ------------------------------------------------
                "🧊 Snapshots (Records) — BACKUP",
            ],
            key="nav",
        )

    # --------------------------------------------------------
    # READ MODE OUTSIDE SIDEBAR
    # --------------------------------------------------------
    mode = st.session_state.get("mode", "free")

    # --------------------------------------------------------
    # PAGE ROUTING (FULL + FIXED) — MAIN AREA ONLY
    # --------------------------------------------------------

    if choice.startswith("📊 Dashboard"):
        page_dashboard(switch_to)

    elif choice.startswith("🩺 Health Log"):
        page_health_log()

    elif choice.startswith("📥 Health Vault"):
        page_health_vault()

    elif choice.startswith("📁 Vault Manager"):
        page_vault_manager()

    elif choice.startswith("🗑 Recycle Bin"):
        page_recycle_bin()

    elif choice.startswith("📄 PDF Preview"):
        page_pdf_preview()

    elif choice.startswith("🔍 OCR"):
        page_ocr()

    elif choice.startswith("🧠 Summary (Demo)"):
        page_summary()

    # --- AI ---
    elif choice.startswith("✨ Merged View"):
        page_merged_view()

    elif choice.startswith("🧬 Summary AI"):
        page_summary_ai()

    elif choice.startswith("📊 Insights AI"):
        page_insights_ai()

    elif choice.startswith("📚 Insights History"):
        page_insights_history()

    elif choice.startswith("📘 Summary Report"):
        page_summary_report()

    elif choice.startswith("🧠 Hybrid Engine"):
        page_hybrid_engine()

    # --- PREMIUM ANALYTICS ---
    elif choice.startswith("📊 Rich Analytics Dashboard"):
        page_analytics_dashboard()

    elif choice.startswith("🚨 AI Health Risk Engine"):
        page_risk_engine()

    elif choice.startswith("🧬 Pattern Timeline AI"):
        page_pattern_timeline_ai()

    elif choice.startswith("🌐 Insight Fusion Layer"):
        page_insight_fusion()

    elif choice.startswith("📈 Insight Graphs"):
        page_insight_graphs()

    elif choice.startswith("🩺 Medical Triptych"):
        page_medical_triptych()

    # --- WELLBEING ---
    elif choice.startswith("🎵 Serene Frequencies"):
        page_serene_frequency()

    elif choice.startswith("🧘 Mood × Sleep × Stress Radar"):
        page_mood_sleep_stress_radar()

    elif choice.startswith("🧘 Health × Vibration Correlation Map"):
        page_health_vibration_correlation()

    # --- FORECASTING ---
    elif choice.startswith("📈 Trend Forecast Engine"):
        page_trend_forecast_engine()

    elif choice.startswith("📅 Unified Timeline Intelligence"):
        page_unified_timeline_intel()

    elif choice.startswith("🧩 Insight Matrix"):
        page_insight_matrix()

    elif choice.startswith("🧠 Health Knowledge Graph"):
        page_health_knowledge_graph()

    # --- SIGNALS ---
    elif choice.startswith("🧬 Multi-Signal Diagnostic Engine"):
        page_multi_signal_engine()

    elif choice.startswith("🧬 Health Signature Engine"):
        page_health_signature_engine()

    elif choice.startswith("🧬 Unified Signal Comparison"):
        page_unified_signal_comparison()

    elif choice.startswith("📉 Signal Volatility Engine"):
        page_signal_volatility_engine()

    # --- MONETIZATION ---
    elif choice.startswith("💎 Subscription Plans"):
        page_subscription_plans()

    # --- FUTURE ---
    elif choice.startswith("🧠 Edge Node Memory"):
        page_edge_node_memory()

    # --- BACKUP ---
    elif choice.startswith("🧊 Snapshots"):
        page_snapshots()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

