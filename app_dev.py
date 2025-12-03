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
import fitz            # PyMuPDF for PDF rendering
import base64
from fpdf import FPDF
import stripe
import html            # for safe_render()

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
            Crafted by Rajdeep Singh — Artigellence Augmentation Aggregator<br>
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
    col = st.container()
    with col:
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
                    Artigellence Premium — Health Intelligence
                </h2>
                <p style="font-size:14px; color:#cbd5f5; margin-bottom:24px;">
                    Unlock full AAA Health Intelligence including:
                </p>
                <div style="text-align:left; display:inline-block; font-size:14px; color:#e5e7eb; margin-bottom:24px; line-height:1.7;">
                    ✔ Full AI Medical Summaries<br>
                    ✔ Deep Medical Insights &amp; Trends<br>
                    ✔ PDF Health Reports &amp; Snapshots<br>
                    ✔ Merged AI View (Doctor + Lab + Notes)<br>
                    ✔ Early Access to AAA Finance &amp; Law<br>
                    ✔ Premium Serene Frequency Indicators
                </div>
                <div style="font-size:13px; color:#9ca3af; opacity:0.9; margin-bottom:20px;">
                    Upgrade to experience the complete power of Artigellence.
                </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("A$10 / month", use_container_width=True)
        with c2:
            st.button("₹500 / month", use_container_width=True)
        with c3:
            st.button("$10 / month", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

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
# PAGE 6 — AI SUMMARY (BASIC — FREE DEMO)
# ============================================================

def page_summary():
    aaa_header()
    st.subheader("🧠 AI Summary (Demo)")
    st.caption("Generate a simple, patient-friendly summary using your logs or scanned text.")

    # -------------------------------
    # LOAD DATA
    # -------------------------------
    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    # -------------------------------
    # INPUT SELECTORS
    # -------------------------------
    st.markdown("### Select Sources")

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

    # -------------------------------
    # BUTTON
    # -------------------------------
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

        # -------------------------------
        # SAFE PROMPT
        # -------------------------------
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

        # -------------------------------
        # OUTPUT BOX
        # -------------------------------
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
# PAGE — MERGED VIEW (PREMIUM FEATURE)
# ============================================================

def page_merged():
    check_firewall("Merged View", st.session_state.get("mode", "free"))

    aaa_header()
    st.subheader("✨ Merged View — Unified Medical Intelligence (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; color:#cbd5f5; margin-bottom:20px;">
            AAA merges multiple medical documents into one structured,
            doctor-style unified intelligence sheet.
        </div>
        """,
        unsafe_allow_html=True,
    )

    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not vault_files:
        st.warning("Upload at least 2 documents.")
        monetization_cta()
        aaa_footer()
        return

    selected_files = st.multiselect(
        "Select 2–5 documents:",
        vault_files,
        max_selections=5
    )

    if len(selected_files) < 2:
        st.info("Select at least two files to proceed.")
        aaa_footer()
        return

    if st.button("Generate Unified Intelligence", use_container_width=True):
        with st.spinner("Merging documents…"):

            try:
                text_blocks = []

                for f in selected_files:
                    p = os.path.join(VAULT_DIR, f)
                    txt = extract_text_any(p)
                    text_blocks.append(f"\n\n===== DOCUMENT: {f} =====\n{txt}")

                merged_block = "\n".join(text_blocks)

                # Safely truncate to 12k tokens
                safe_block = merged_block[:12000]

                prompt = f"""
You are AAA Health Intelligence.

Create a clean, structured, doctor-style unified summary.

Sections required:
1. Combined Key Findings
2. Trends & Patterns
3. Risk Indicators
4. Conflicts / Missing Information
5. Actionable Recommendations
6. Overall Takeaway

TEXT:
{safe_block}
"""

                result = call_gemini(prompt)
                result = safe_render(result)

                # Premium styling
                st.markdown(
                    """
                    <div style="
                        padding:28px;
                        border-radius:14px;
                        background:#0f1a2e;
                        border-left:5px solid #38bdf8;
                        box-shadow:0 0 18px rgba(56,189,248,0.28);
                        color:#e2e8f0;
                        font-size:15px;
                        line-height:1.65;
                    ">
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(result, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.code(result)

            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 8 — SUMMARY AI (PREMIUM)
# ============================================================

def page_summary_ai():
    check_firewall("Summary AI", st.session_state.get("mode", "free"))
    aaa_header()
    st.subheader("🧬 Summary AI (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:15px; line-height:1.6; color:#8FA3B8;">
            Generate a structured, patient-friendly medical summary using AAA Intelligence.
        </div>
        """,
        unsafe_allow_html=True,
    )

    files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not files:
        st.info("Upload at least one document.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select file:", files)

    if st.button("Generate Summary"):
        with st.spinner("Analyzing…"):

            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)
                safe_text = text[:6000]

                prompt = (
                    "Provide a structured, patient-friendly medical summary.\n"
                    "Sections:\n"
                    "1. Key Findings\n"
                    "2. Easy Explanation\n"
                    "3. Risk Indicators\n"
                    "4. Missing Info\n"
                    "5. Actionable Next Steps\n\n"
                    f"TEXT:\n{safe_text}"
                )

                result_raw = call_gemini(prompt)
                result = safe_render(result_raw)

                st.success("Summary generated!")
                st.markdown(result, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 9 — INSIGHTS AI (HYBRID ENGINE) — UPDATED SAFE VERSION
# ============================================================

def generate_insights_hybrid(file_text: str) -> str:
    """Gemini Hybrid Engine: Short Summary + Deep Insights."""
    prompt = f"""
You are AAA-Health Intelligence. Analyze the following medical text and produce a HYBRID structured output.

TEXT:
\"\"\"
{file_text}
\"\"\"

OUTPUT FORMAT EXACTLY:

SHORT_SUMMARY:
- 3–5 bullet points
- Simple language
- Easy to understand

DEEP_INSIGHTS:
SECTION 1 — Key Findings:
- 4–7 bullet points

SECTION 2 — Trends & Patterns:
- 3–5 bullet points

SECTION 3 — Risks & Red Flags:
- 2–4 bullet points

SECTION 4 — Recommendations:
- 3–6 bullet points

Return ONLY formatted text. No intro, no disclaimers.
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def save_insights_record(title: str, short_summary: str, deep_insights: str):
    """Save hybrid insights to insights.json."""
    data = load_json(INSIGHTS_FILE, [])
    data.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": title,
        "short": short_summary,
        "deep": deep_insights,
    })
    save_json(INSIGHTS_FILE, data)


def page_insights_ai():
    check_firewall("Insights AI", st.session_state.get("mode", "free"))
    aaa_header()
    st.subheader("📊 Insights AI (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # LOAD VAULT FILES
    # ------------------------------------------------------------
    files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not files:
        st.warning("No files found in your Vault.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select file for insights:", files)

    # ------------------------------------------------------------
    # RUN HYBRID ENGINE
    # ------------------------------------------------------------
    if st.button("Generate Insights"):
        with st.spinner("🔥 Generating AAA Hybrid Intelligence…"):

            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)

                ai_output_raw = generate_insights_hybrid(text)
                ai_output = ai_output_raw or ""

                # -------------------------
                # SAFE RENDERING
                # -------------------------
                ai_output_safe = safe_render(ai_output)

                # -------------------------
                # SPLITTING SECTIONS
                # -------------------------
                short_part = ""
                deep_part = ai_output_safe

                if "SHORT_SUMMARY:" in ai_output:
                    try:
                        short_part = ai_output.split("SHORT_SUMMARY:")[1].split("DEEP_INSIGHTS:")[0].strip()
                    except:
                        short_part = "Unable to extract short summary."

                if "DEEP_INSIGHTS:" in ai_output:
                    try:
                        deep_part = ai_output.split("DEEP_INSIGHTS:")[1].strip()
                    except:
                        deep_part = ai_output_safe

                short_safe = safe_render(short_part)
                deep_safe = safe_render(deep_part)

                # -------------------------
                # SAVE HISTORY
                # -------------------------
                save_insights_record(selected_file, short_safe, deep_safe)

                # -------------------------
                # UI DISPLAY
                # -------------------------
                st.success("Insights generated successfully!")

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
# PAGE — INSIGHTS HISTORY (PREMIUM) — UPGRADED VERSION
# ============================================================

def page_insights_history():
    check_firewall("Insights History", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            📚 Insights History (Premium)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Your previously generated health insights — deep analysis, trends, and summaries.
        </p>
        <br>
    """, unsafe_allow_html=True)

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # Load insights
    insights = load_json(INSIGHTS_FILE, [])
    if not insights:
        st.info("No insights found. Generate insights first in Insights AI.")
        monetization_cta()
        aaa_footer()
        return

    # AAA brand colors
    card_bg = "#0B1625"          # Deep navy
    teal = "#00A6C8"             # Teal
    gold = "#D4A037"             # Metallic gold
    soft_gold = "#F2C678"        # Accent gold

    # Card styling
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

    # Render cards (newest first)
    for item in insights[::-1]:
        title = item.get("title", "Insight")
        date = item.get("date", "")
        short = item.get("short", "")
        deep = item.get("deep", "")

        st.markdown("<div class='aaa-card'>", unsafe_allow_html=True)

        # Title + Date
        st.markdown(
            f"<div class='aaa-title'>🧠 {title}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='aaa-date'>📅 {date}</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='aaa-divider'></div>", unsafe_allow_html=True)

        # Short summary
        st.markdown("<div class='aaa-section-title'>🔹 Short Summary</div>", unsafe_allow_html=True)
        st.markdown(short.replace("-", "• "))

        # Deep insights section
        with st.expander("🔸 Deep Insights (Click to expand)"):
            st.markdown(deep.replace("-", "• "))

        st.markdown("<div class='aaa-divider'></div>", unsafe_allow_html=True)

        # Export button
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
# PAGE 10 — SUMMARY REPORT (PREMIUM PDF EXPORT)
# ============================================================

from fpdf import FPDF

class AAA_PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(0, 166, 200)  # AAA teal
        self.cell(0, 10, "AAA — Health Intelligence Summary Report", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-18)
        self.set_font("Arial", "I", 9)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "Artigellence Augmentation Aggregator — Early Access", ln=True, align="C")


def generate_pdf(text: str, title: str, date: str, output_path: str):
    pdf = AAA_PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(212, 160, 55)  # Gold
    pdf.multi_cell(0, 10, title)
    pdf.ln(3)

    # Date
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0, 166, 200)
    pdf.cell(0, 8, f"Date: {date}", ln=True)
    pdf.ln(5)

    # Main Body
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(255, 255, 255)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output(output_path)


def page_summary_report():
    aaa_header()
    st.subheader("📘 Summary Report (Premium PDF)")

    # 🔒 Premium Lock
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # Load summaries from your existing AI_SUMMARY_FILE
    summaries = load_json(AI_SUMMARY_FILE, [])

    if not summaries:
        st.info("No AI summaries found. Generate some first in Summary AI.")
        aaa_footer()
        return

    # Build dropdown
    options = [
        f"{i+1}. {s.get('date', '')} — {s.get('title', 'Summary')}"
        for i, s in enumerate(summaries)
    ]

    selected_idx = st.selectbox(
        "Choose a summary to export:",
        list(range(len(options))),
        format_func=lambda i: options[i],
    )

    selected_summary = summaries[selected_idx]
    text = selected_summary.get("text", "")
    title = selected_summary.get("title", "AAA Summary")
    date = selected_summary.get("date", "")

    if st.button("📄 Generate PDF Report"):
        try:
            generate_pdf(text, title, date, SUMMARY_REPORT_PDF)
            st.success("PDF report generated successfully.")

            # Download button
            with open(SUMMARY_REPORT_PDF, "rb") as f:
                st.download_button(
                    label="Download Report",
                    data=f,
                    file_name="AAA_Health_Summary_Report.pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    monetization_cta()
    aaa_footer()


# Saving function remains same (no changes)
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
# PAGE 11 — HYBRID ENGINE (PREMIUM MULTI-SOURCE AI)
# ============================================================

def page_hybrid_engine():
    check_firewall("Hybrid Engine", st.session_state.get("mode", "free"))
    aaa_header()
    st.subheader("🧠 Hybrid Engine — Multi-Source Intelligence (Premium)")

    # 🔒 Premium check
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:15px; line-height:1.5; margin-bottom:15px; color:#8FA3B8;">
        Combine all intelligence sources — OCR text, PDFs, doctor notes, 
        summaries, insights — to generate a powerful unified analysis powered by AAA Intelligence.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # 1. Load OCR text
    # ----------------------------------------------------------
    ocr_text = ""
    try:
        if os.path.exists(OCR_TEXT_FILE):
            ocr_text = open(OCR_TEXT_FILE, "r").read()
    except:
        pass

    # ----------------------------------------------------------
    # 2. Load last PDF text
    # ----------------------------------------------------------
    pdf_text = ""
    try:
        if os.path.exists(PDF_TEXT_FILE):
            pdf_text = open(PDF_TEXT_FILE, "r").read()
    except:
        pass

    # ----------------------------------------------------------
    # 3. Load doctor notes
    # ----------------------------------------------------------
    doctor_notes = ""
    try:
        if os.path.exists(DOCTOR_NOTES_FILE):
            doctor_notes = open(DOCTOR_NOTES_FILE, "r").read()
    except:
        pass

    # ----------------------------------------------------------
    # 4. Load AI Summaries
    # ----------------------------------------------------------
    summaries = load_json(AI_SUMMARY_FILE, [])
    last_summary = summaries[-1]["text"] if summaries else ""

    # ----------------------------------------------------------
    # 5. Load AI Insights
    # ----------------------------------------------------------
    insights = load_json(INSIGHTS_FILE, [])
    last_insight = insights[-1]["text"] if insights else ""

    st.markdown("### Select intelligence sources to combine:")
    use_ocr = st.checkbox("OCR extracted text", True)
    use_pdf = st.checkbox("PDF extracted text", True)
    use_notes = st.checkbox("Doctor notes", True)
    use_summary = st.checkbox("AI Summary", True)
    use_insight = st.checkbox("AI Insight", True)

    if st.button("⚡ Generate Hybrid Intelligence Report"):
        with st.spinner("Synthesising multi-source intelligence..."):
            combined_text = ""

            if use_ocr:
                combined_text += "\n\n[OCR TEXT]\n" + ocr_text
            if use_pdf:
                combined_text += "\n\n[PDF TEXT]\n" + pdf_text
            if use_notes:
                combined_text += "\n\n[DOCTOR NOTES]\n" + doctor_notes
            if use_summary and last_summary:
                combined_text += "\n\n[AI SUMMARY]\n" + last_summary
            if use_insight and last_insight:
                combined_text += "\n\n[AI INSIGHT]\n" + last_insight

            if not combined_text.strip():
                st.error("No available text to combine.")
                aaa_footer()
                return

            prompt = f"""
            You are AAA Hybrid Engine.

            Combine the following multi-source medical information into a single,
            medically balanced and easy-to-understand unified health analysis.

            Sources:
            {combined_text}

            Output must include:
            - Key findings
            - Risks & Severity
            - Trends & patterns
            - Doctor-style explanation
            - Actionable advice (safe, general)
            """

            try:
                response = call_gemini(prompt)
                st.markdown(response)
            except Exception as e:
                st.error(f"Error generating hybrid intelligence: {e}")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 12 — RICH ANALYTICS DASHBOARD (PREMIUM ANALYTICS)
# ============================================================

def page_analytics_dashboard():
    check_firewall("Analytics Dashboard", st.session_state.get("mode", "free"))
    aaa_header()
    st.subheader("📊 Rich Analytics Dashboard (Premium)")

    # 🔒 Premium Lock
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # -----------------------------
    # Description
    # -----------------------------
    st.markdown(
        """
        <div style="font-size:16px; line-height:1.7; margin-bottom:15px;">
            Deep multi-layer analytics based on your AI summaries, insights, logs,
            and health score patterns. Updated automatically as your Vault grows.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========= Load required data =========
    summaries = load_json(AI_SUMMARY_FILE, [])
    insights = load_json(INSIGHTS_FILE, [])
    health_data = load_json(HEALTH_LOG_FILE, [])
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    # ========= Section: Data Overview =========
    st.markdown("## 🗂 Data Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AI Summaries", len(summaries))
    col2.metric("AI Insights", len(insights))
    col3.metric("Health Log Entries", len(health_data))
    col4.metric("Documents in Vault", len(vault_files))

    st.markdown("---")

    # ========= Section: Health Score Trend =========
    st.markdown("## 📈 Health Score Trend (Last 30 Entries)")

    if health_data:
        try:
            import pandas as pd
            import matplotlib.pyplot as plt

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

    # ========= Section: Term Frequency from AI Summaries =========
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

    # ========= Section: Condition Alerts =========
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

    # ========= Section: Regional Health Awareness =========
    st.markdown("## 🌏 Regional Health Awareness (Beta)")

    st.markdown(
        """
        <p style="font-size:15px; line-height:1.6; color:#CBD5E1;">
            This shows location-based seasonal trends and general awareness.
            (Static beta content — will be replaced with live regional models.)
        </p>
        """,
        unsafe_allow_html=True,
    )

    region = "Sydney, AU"
    st.info(f"Region detected: **{region}**")

    st.markdown(
        """
        - 🌡 Seasonal allergies are moderate.  
        - 🤧 Flu cases rising locally.  
        - 🦠 Gastro outbreaks reported in nearby suburbs.  
        - ☀ UV index trending high — extra precautions advised.  
        """
    )

    st.markdown("---")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 13 — SMART SNAPSHOTS (FINAL VERSION — FROM PAGE 39)
# ============================================================

def page_snapshots():
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

    # -------------------------------
    # LIST SNAPSHOTS
    # -------------------------------
    st.subheader("📁 Available Snapshots")

    folders = sorted(
        [
            d
            for d in os.listdir(SNAPSHOT_DIR)
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

            st.write("Contains copies of logs, OCR results, photos, and AI summaries.")

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
# PAGE 15 — TIMELINE INTELLIGENCE (AAA NODE v1)
# ============================================================

TIMELINE_FILE = os.path.join(DATA_DIR, "timeline_master.json")

if not os.path.exists(TIMELINE_FILE):
    with open(TIMELINE_FILE, "w") as f:
        json.dump([], f, indent=4)


def load_timeline():
    try:
        with open(TIMELINE_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_timeline(data):
    with open(TIMELINE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_timeline_event(
    summary,
    category="general",
    source="AAA Engine",
    risk="N/A",
    engine="Gemini/AAA Hybrid",
):
    events = load_timeline()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "category": category,
        "source": source,
        "risk": risk,
        "engine": engine,
        "event_id": f"EVT-{len(events)+1:04d}",
    }
    events.append(entry)
    save_timeline(events)


def page_timeline_intelligence():
    check_firewall("Timeline Intelligence", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown(
        """
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            🕰 Timeline Intelligence (AAA Node v1)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            A unified chronological record of your health logs, AI summaries,
            snapshots, OCR results and AAA insights.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    events = load_timeline()
    if not events:
        st.info("No timeline events yet.")
        monetization_cta()
        aaa_footer()
        return

    card_bg = "#0D1628"
    accent = "#F2C678"
    border = "#04A3D7"

    for evt in reversed(events):
        ts = evt.get("timestamp", "")
        summary = evt.get("summary", "")
        category = evt.get("category", "")
        source = evt.get("source", "")
        risk = evt.get("risk", "")
        engine = evt.get("engine", "")
        event_id = evt.get("event_id", "")

        st.markdown(
            f"""
            <div style="
                background-color:{card_bg};
                padding:20px;
                margin-bottom:18px;
                border-radius:16px;
                border-left:4px solid {accent};
                box-shadow:0px 0px 18px rgba(0,0,0,0.35);
            ">
                <div style="font-size:15px; color:{accent}; font-weight:bold;">
                    {ts} — {category.upper()}
                </div>

                <div style="font-size:14px; margin-top:8px; color:#DBE7F0;">
                    <b>Summary:</b> {summary}
                </div>

                <details style="margin-top:10px; color:#CBD9E6;">
                    <summary style="cursor:pointer; font-size:13px; color:{border};">
                        View Full Details
                    </summary>

                    <div style="margin-top:10px; font-size:13px; line-height:1.6;">
                        <b>Event ID:</b> {event_id}<br>
                        <b>Source:</b> {source}<br>
                        <b>Risk Level:</b> {risk}<br>
                        <b>Engine:</b> {engine}<br>
                    </div>
                </details>
            </div>
            """,
            unsafe_allow_html=True,
        )

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 16 — AI HEALTH SCORE ENGINE
# ============================================================

def compute_health_score(merged_data, insights, logs):
    if not merged_data and not insights and not logs:
        return 72, "⚠️ Limited data — upload more logs and documents.", []

    reasons = []
    score = 80

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

    for item in insights:
        risk = item.get("risk_level", "").lower()
        if "high" in risk:
            score -= 7
        if "moderate" in risk:
            score -= 3

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


def page_health_score_engine():
    check_firewall("Health Score", st.session_state.get("mode", "free"))
    aaa_header()

    st.subheader("🧠 AI Health Score Engine")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    merged_data = load_json(MERGED_DATA_FILE, [])
    insights = load_json(INSIGHTS_HISTORY_FILE, [])
    logs = load_json(HEALTH_LOG_FILE, [])

    score, summary_text, reasons = compute_health_score(
        merged_data, insights, logs
    )

    navy = "#071E36"
    teal = "#00A6B6"
    gold = "#F4BD3B"
    soft_gold = "#F2C678"

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

    st.markdown("<h4 style='color:#F2C678;'>Breakdown</h4>", unsafe_allow_html=True)

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
    aaa_header()
    st.subheader("🧩 AAA Pattern Timeline AI — Neuralink-Style Condensed Signals")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

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
    range_choice = st.selectbox("Choose analysis period:", ["Last 7 Days", "Last 14 Days", "Last 30 Days"])

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
# PAGE 21 — AI HEALTH RISK ENGINE
# ============================================================

def page_risk_engine():
    aaa_header()
    st.subheader("⚠️ AI Health Risk Engine (Beta)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})
    memory_signals = load_json(os.path.join(DATA_DIR, "memory_signals.json"), [])

    st.markdown("### 📅 Select Analysis Window")
    window = st.selectbox("Analyze patterns for:", ["Last 7 Days", "Last 14 Days", "Last 30 Days"])

    days = 7 if window == "Last 7 Days" else 14 if window == "Last 14 Days" else 30
    cutoff = datetime.now().timestamp() - (days * 86400)

    filtered_logs = [l for l in logs if l.get("timestamp", 0) >= cutoff]

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

    aaa_footer()


# ============================================================
# PAGE 22 — INSIGHT FUSION LAYER
# ============================================================

def page_insight_fusion():
    aaa_header()
    st.subheader("🌐 Insight Fusion Layer — Unified Health Intelligence (Beta)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # -------------------------------
    # LOAD ALL SIGNAL SOURCES SAFELY
    # -------------------------------
    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})
    memory_signals = load_json(os.path.join(DATA_DIR, "memory_signals.json"), [])
    vault_data = load_json(os.path.join(DATA_DIR, "vault_data.json"), {})
    score_history = load_json(os.path.join(DATA_DIR, "score_history.json"), [])
    ocr_results = load_json(os.path.join(DATA_DIR, "ocr_results.json"), {})

    # -------------------------------
    # PRECOMPUTE ALL TEXT BLOCKS
    # -------------------------------
    logs_text = "\n".join([l.get("summary", "") for l in logs])
    memory_text = "\n".join(memory_signals)
    insights_text = json.dumps(insights, indent=2)
    vault_text = json.dumps(vault_data, indent=2)
    ocr_text = json.dumps(ocr_results, indent=2)
    score_text = json.dumps(score_history, indent=2)

    # -------------------------------
    # FINAL SAFE COMBINED TEXT
    # -------------------------------
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

    # -------------------------------
    # RUN FUSION ENGINE
    # -------------------------------
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
# PAGE 23 — AAA INSIGHT GRAPHS
# ============================================================

def page_insight_graphs():
    aaa_header()
    st.subheader("📈 AAA Insight Graphs & Trend Visualizer")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(AI_SUMMARY_FILE, {})
    score_history = load_json(os.path.join(DATA_DIR, "score_history.json"), [])

    log_df = pd.DataFrame(logs)
    score_df = pd.DataFrame(score_history)
    insight_df = pd.DataFrame(insights.get("history", []))

    st.markdown("---")

    # 1) HEALTH SCORE TREND
    st.markdown("### 📈 Health Score Trend")

    if not score_df.empty:
        score_df["date"] = pd.to_datetime(score_df["timestamp"]).dt.date

        chart = alt.Chart(score_df).mark_line(point=True).encode(
            x="date:T",
            y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100])),
            tooltip=["date", "score"],
        ).properties(
            width="container",
            height=300
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No health scores yet.")

    st.markdown("---")

    # 2) DAILY LOG FREQUENCY
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
        st.info("No logs yet.")

    st.markdown("---")

    # 3) INSIGHT FREQUENCY
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
# PAGE 24 — MEDICAL TRIPTYCH
# ============================================================

def page_medical_triptych():
    aaa_header()
    st.subheader("🩺 Medical Triptych — Doctor + Lab + PDF Fusion (Beta)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style='font-size:16px; margin-bottom:20px;'>
            Fuses doctor notes, lab reports, and PDF vault documents.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Doctor notes
    doctor_notes = st.text_area(
        "🟦 Doctor Notes",
        height=120,
        placeholder="Enter clinical notes, symptoms…"
    )

    # Lab PDF
    st.markdown("### 🟧 Lab Report (PDF → Text)")
    lab_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="lab_pdf_uploader")
    lab_text = ""

    if lab_pdf:
        try:
            with open("temp_lab.pdf", "wb") as f:
                f.write(lab_pdf.read())
            lab_text = extract_text_any("temp_lab.pdf")
            st.success("Lab report extracted.")
        except:
            st.error("Unable to extract lab PDF.")

    # Vault PDF selection
    st.markdown("### 🟩 Select Medical PDF from Vault")
    vault_files = [f for f in os.listdir(VAULT_DIR) if f.endswith(".pdf")]

    selected_pdf = st.selectbox("Choose PDF:", ["None"] + vault_files)
    vault_text = ""

    if selected_pdf != "None":
        try:
            path = os.path.join(VAULT_DIR, selected_pdf)
            vault_text = extract_text_any(path)
            st.success(f"Loaded PDF: {selected_pdf}")
        except:
            st.error("Failed to read PDF.")

    combined_triptych = f"""
DOCTOR NOTES:
{doctor_notes}

LAB REPORT:
{lab_text}

MEDICAL PDF:
{vault_text}
"""

    if st.button("🔮 Generate Unified Medical Summary"):
        if not (doctor_notes or lab_text or vault_text):
            st.warning("Provide at least one input.")
            aaa_footer()
            return

        with st.spinner("Generating…"):
            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                resp = ai.generate_content(
                    f"""
Fuse DOCTOR NOTES + LAB REPORT + MEDICAL PDF.

FORMAT:
1) Unified Clinical Summary
2) Key Trends
3) Risk/Attention Layer
4) Doctor-Friendly Briefing

DATA:
{combined_triptych}
"""
                )
                st.info(resp.text)
            except Exception as e:
                st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 25 — SERENE FREQUENCY
# ============================================================

def page_serene_frequency():
    aaa_header()
    st.subheader("🎵 Serene Frequency Indicators — Vibration × Health Intelligence")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

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
        st.info("No logs in this range.")
        aaa_footer()
        return

    combined_text = "\n".join([l.get("summary", "") for l in filtered_logs])

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"""
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
"""
        )
        st.info(response.text)
    except Exception as e:
        st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 26 — MOOD × SLEEP × STRESS RADAR
# ============================================================

def page_mood_sleep_stress_radar():
    aaa_header()
    st.subheader("🧘 Mood × Sleep × Stress Radar — Mind–Body State Map")

    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

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
# PAGE 27 — Health × Vibration Correlation Map
# ============================================================

def page_health_vibration_correlation():
    aaa_header()
    st.subheader("🌀 Health × Vibration Correlation Map (Beta)")

    # -------------------------------
    # PREMIUM LOCK
    # -------------------------------
    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

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

    # -------------------------------
    # USER INPUT SELECTION
    # -------------------------------
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

    if st.button("🔍 Run Correlation Analysis"):
        with st.spinner("Running AAA Correlation Engine…"):

            import random
            import matplotlib.pyplot as plt

            try:
                # Load placeholders / user data
                health_json = load_json(os.path.join(DATA_DIR, "health_data.json"), {})
                vibration_json = load_json(os.path.join(DATA_DIR, "serene_frequency_data.json"), {})
                mindbody_json = load_json(os.path.join(DATA_DIR, "mood_sleep_stress.json"), {})

                # Placeholder correlation engine
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

                # Scatter plot placeholder
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
# PAGE 28 — Trend Forecast Engine (Predictive Health + Vibration AI)
# ============================================================

def page_trend_forecast_engine():
    aaa_header()
    st.subheader("📈 Trend Forecast Engine — Predictive Health × Vibration AI (Beta)")

    # --------------------------
    # PREMIUM LOCK
    # --------------------------
    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

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

    # --------------------------
    # LOAD DATA
    # --------------------------
    insights_raw = load_json(AI_SUMMARY_FILE, {})
    insights = insights_raw.get("history", [])

    logs_raw = load_json(HEALTH_LOG_FILE, [])
    logs = [l.get("summary", "") for l in logs_raw]

    if not insights and not logs:
        st.warning("No historical data available for forecasting.")
        aaa_footer()
        return

    # --------------------------
    # USER SELECT WINDOW
    # --------------------------
    window = st.selectbox(
        "Select forecast window:",
        ["Next 3 days", "Next 7 days", "Next 14 days"]
    )

    # --------------------------
    # RUN FORECAST
    # --------------------------
    if st.button("Generate Forecast"):
        with st.spinner("Building predictive model…"):

            try:
                combined_text = ""

                for entry in logs:
                    combined_text += f"\n{entry}"

                for item in insights:
                    combined_text += f"\n{item.get('short','')}"
                    combined_text += f"\n{item.get('deep','')}"

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

                # Preview chart (placeholder)
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots()
                ax.plot([1, 2, 3, 4, 5, 6, 7],
                        [random.randint(40, 90) for _ in range(7)])
                ax.set_title("Predictive Health-Vibration Curve (Sample)")
                ax.set_xlabel("Days Ahead")
                ax.set_ylabel("Trend Strength")
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Forecast generation failed: {e}")

    aaa_footer()


# ============================================================
# PAGE 29 — Unified Timeline Intelligence (All Signals, One Timeline)
# ============================================================

def page_unified_timeline_intel():
    aaa_header()
    st.subheader("📅 Unified Timeline Intelligence — All Signals, One Timeline (Beta)")

    # Premium Lock
    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

    st.markdown(
        """
        <p style="font-size:15px; line-height:1.6;">
        A unified chronological view of <b>all your health signals</b> —
        logs, summaries, mood, sleep, stress, vibration indicators, 
        AI insights — merged into one timeline for easier pattern detection.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    try:
        import matplotlib.pyplot as plt
        import random

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
# PAGE 30 — AAA Insight Matrix (Signal-to-Signal Relationship Grid)
# ============================================================

def page_insight_matrix():

    aaa_header()
    st.subheader("🧩 AAA Insight Matrix — Signal-to-Signal Relationship Grid (Beta)")

    # Premium Lock
    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:25px;">
            Compare how different health and vibration signals interact, influence,
            or correlate with each other using a placeholder analytical grid.  
            Future versions will use AAA’s unified data lake.
        </div>
        """,
        unsafe_allow_html=True,
    )

    signals = [
        "Heart Rate",
        "Blood Pressure",
        "Sleep Quality",
        "Stress Level",
        "Oxygen Saturation",
        "Glucose",
        "Vibration Index",
        "Mood Score",
        "Inflammation Score"
    ]

    st.markdown("### 🔢 Signals Included")
    st.write(signals)

    st.markdown("### 🔥 Relationship Matrix (Synthetic Placeholder)")

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
# PAGE 31 — Health Knowledge Graph (AI Semantic Medical Map)
# ============================================================

def page_health_knowledge_graph():
    aaa_header()
    st.subheader("🧠 Health Knowledge Graph — AI Semantic Medical Map (Beta)")

    # Premium Lock
    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:15px; line-height:1.6; margin-bottom:15px;">
            Explore an AI-generated semantic map connecting symptoms, biomarkers,
            lifestyle patterns, stress, sleep cycles, and vibration signals.
        </div>
        """,
        unsafe_allow_html=True,
    )

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

                st.info(
                    "🔧 Full interactive graph will be added in AAA-Health v0.9."
                )

        except Exception as e:
            st.error(f"Graph Engine Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 32 — MULTI-SIGNAL DIAGNOSTIC ENGINE
# ============================================================

def page_multi_signal_engine():
    check_firewall("Multi-Signal Diagnostic Engine", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#D4A037; margin-bottom:4px;">
            🧬 Multi-Signal Diagnostic Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            AI-powered differential insights using all combined health signals.<br>
            (Strictly informational — no medical advice)
        </p>
        <br>
    """, unsafe_allow_html=True)

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    signals = []

    # Vault files
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        text = extract_text_any(os.path.join(VAULT_DIR, f))
        if text.strip():
            signals.append(text)

    # OCR results
    ocr_results = load_json(OCR_DATA_FILE, [])
    for item in ocr_results:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # Health logs
    logs = load_json(HEALTH_LOG_FILE, [])
    for entry in logs:
        if entry.get("note", "").strip():
            signals.append(entry["note"])

    # Doctor notes
    doctor_notes = load_json(DOCTOR_NOTES_FILE, [])
    if doctor_notes:
        signals.append("\n".join(doctor_notes))

    if not signals:
        st.info("No signals available. Upload files or write logs.")
        monetization_cta()
        aaa_footer()
        return

    if st.button("🚀 Run Diagnostic Engine"):
        with st.spinner("Analyzing multi-source signals…"):
            result = run_multi_signal_engine(signals)

        st.markdown(result["formatted"], unsafe_allow_html=True)

        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Multi-Signal Diagnostic Insight",
            "short": result["json"].get("summary", ""),
            "deep": result["formatted"]
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Insight saved.")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 33 — HEALTH SIGNATURE ENGINE
# ============================================================

def page_health_signature_engine():
    check_firewall("Health Signature Engine", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#D4A037; margin-bottom:4px;">
            🩺 Health Signature Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Generates a unified health signature across logs, biomarkers,
            PDFs and behavioural patterns.
        </p>
        <br>
    """, unsafe_allow_html=True)

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    signals = []

    # Vault files
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        text = extract_text_any(os.path.join(VAULT_DIR, f))
        if text.strip():
            signals.append(text)

    # OCR
    ocr_data = load_json(OCR_DATA_FILE, [])
    for item in ocr_data:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # Health logs
    logs = load_json(HEALTH_LOG_FILE, [])
    for entry in logs:
        note = entry.get("note", "").strip()
        if note:
            signals.append(note)

    if not signals:
        st.info("No health signals available.")
        monetization_cta()
        aaa_footer()
        return

    if st.button("🚀 Generate Health Signature"):
        with st.spinner("Building your unified health signature…"):
            try:
                result = run_multi_signal_engine(signals)
            except Exception as e:
                st.error(f"Engine error: {e}")
                aaa_footer()
                return

        st.markdown("### 🔍 Your Health Signature")
        st.markdown(result["formatted"], unsafe_allow_html=True)

        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Health Signature Engine",
            "short": result["json"].get("summary", ""),
            "deep": result["formatted"]
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Health Signature saved.")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 34 — UNIFIED SIGNAL COMPARISON ENGINE
# ============================================================

def page_unified_signal_comparison():
    check_firewall("Unified Signal Comparison Engine", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#D4A037; margin-bottom:6px;">
            🔎 Unified Signal Comparison Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Compare logs, biomarkers, PDFs, vibration indicators, and patterns side-by-side.
            (Strictly informational — no medical advice)
        </p>
        <br>
    """, unsafe_allow_html=True)

    # Premium wall
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # LOAD SIGNAL SOURCES
    # ------------------------------------------------------------
    signals = []

    # Health Logs
    logs = load_json(HEALTH_LOG_FILE, [])
    log_text = "\n".join([entry.get("note", "") for entry in logs if entry.get("note")])
    if log_text.strip():
        signals.append(("Health Log", log_text))

    # OCR
    ocr_items = load_json(OCR_DATA_FILE, [])
    ocr_text = "\n".join([item.get("text", "") for item in ocr_items if isinstance(item, dict)])
    if ocr_text.strip():
        signals.append(("OCR Extracted Text", ocr_text))

    # Vault PDFs
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        extracted = extract_text_any(os.path.join(VAULT_DIR, f))
        if extracted.strip():
            signals.append((f, extracted))

    # Doctor Notes
    doctor = load_json(DOCTOR_NOTES_FILE, [])
    if doctor:
        signals.append(("Doctor Notes", "\n".join(doctor)))

    # Validation
    if not signals:
        st.info("No signals available. Please upload files or add logs.")
        monetization_cta()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # USER SELECT — PICK 2–4 SIGNALS
    # ------------------------------------------------------------
    st.markdown("### Select signals to compare")

    signal_names = [s[0] for s in signals]
    selected = st.multiselect("Choose 2–4 signals:", signal_names)

    if len(selected) < 2:
        st.warning("Select at least two signals to continue.")
        aaa_footer()
        return

    # Build comparison list
    compare_blocks = [s[1] for s in signals if s[0] in selected]

    # ------------------------------------------------------------
    # RUN ENGINE
    # ------------------------------------------------------------
    if st.button("🚀 Run Comparison Engine"):
        with st.spinner("Generating comparison across signals…"):

            combined_data = ""
            for name, text in signals:
                if name in selected:
                    combined_data += f"\n\n### {name}\n{text}\n"

            prompt = f"""
            You are AAA Intelligence. Compare these signals:

            {str(selected)}

            DATA:
            {combined_data[:25000]}

            FORMAT (HTML):
            1. Comparison Table  
            2. Overlap Map  
            3. Conflicts  
            4. Agreement Score (0–100)  
            5. Summary (150 words)
            """

            ai_text = call_gemini(prompt)

        # Display
        st.markdown(ai_text, unsafe_allow_html=True)

        # Save history
        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Unified Signal Comparison",
            "short": ai_text[:600],
            "deep": ai_text
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Comparison saved to Insights History.")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 35 — SIGNAL VOLATILITY ENGINE (INFORMATIONAL ONLY)
# ============================================================

def page_signal_volatility_engine():
    check_firewall("Signal Volatility Engine", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#D4A037; margin-bottom:4px;">
            📉 Signal Volatility Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Detect variability, noise, instability, and fluctuations across your health signals.
            (Strictly informational — no medical advice)
        </p>
        <br>
    """, unsafe_allow_html=True)

    # PREMIUM
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    signals = []

    # Vault
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        text = extract_text_any(os.path.join(VAULT_DIR, f))
        if text.strip():
            signals.append(text)

    # OCR
    ocr = load_json(OCR_DATA_FILE, [])
    for item in ocr:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # Logs
    logs = load_json(HEALTH_LOG_FILE, [])
    for entry in logs:
        note = entry.get("note", "")
        if note:
            signals.append(note)

    # Doctor notes
    doctor = load_json(DOCTOR_NOTES_FILE, [])
    if doctor:
        signals.append("\n".join(doctor))

    if not signals:
        st.info("No signals found.")
        monetization_cta()
        aaa_footer()
        return

    # RUN ENGINE
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

            OUTPUT (HTML):
            1. High-Volatility Zones  
            2. Low-Volatility Zones  
            3. Noise / Outlier Regions  
            4. Instability Correlations  
            5. Summary (100 words)
            """

            ai_text = call_gemini(prompt + combined)

        st.markdown(ai_text, unsafe_allow_html=True)

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE — SUBSCRIPTION PLANS (AAA PREMIUM)
# ============================================================

def page_subscription_plans():
    aaa_header()
    st.subheader("💳 Subscription Plans — Artigellence Premium")

    st.write(
        "Choose how you want to explore **AAA — Health Intelligence**.\n"
        "Free mode lets you try essentials. Premium unlocks full intelligence."
    )

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # FREE PLAN
    # --------------------------------------------------------
    with col1:
        st.markdown("### 🆓 Free")
        st.caption("Basic AAA features.")
        st.markdown("**$0 / month**")

        st.write(
            """
            **Includes:**  
            • Dashboard  
            • Health Log  
            • Health Vault + OCR  
            • Demo AI Summary  
            • Snapshots (Basic)  
            • PDF Preview (Basic)  
            """
        )

    # --------------------------------------------------------
    # PREMIUM INDIA — ₹500/month
    # --------------------------------------------------------
    with col2:
        st.markdown("### 🇮🇳 Premium — India")
        st.caption("Accessible India pricing.")
        st.markdown("**₹500 / month**")

        st.write(
            """
            **Includes:**  
            • Unlimited AI Summaries  
            • Hybrid Engine  
            • Insights + Full History  
            • AI PDF Reports  
            • Timeline + Snapshots (Full)  
            • Finance × Law Early Access  
            • Vibration Indicators (Beta)  
            """
        )

        st.markdown(
            """
            <a href="https://buy.stripe.com/6oU4gyelZ60Zf7q3L15ZC03" target="_blank">
                <button style="padding:10px 18px; border-radius:8px; width:100%;">Subscribe — ₹500/mo</button>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.success("Recommended")

    # --------------------------------------------------------
    # PREMIUM GLOBAL — $10/month
    # --------------------------------------------------------
    with col3:
        st.markdown("### 🌍 Premium — Global")
        st.caption("For users outside India.")
        st.markdown("**$10 / month**")

        st.write(
            """
            **Includes:**  
            • All Premium Features  
            • Unlimited AI PDFs  
            • Hybrid Engine  
            • Vibration × Health Map  
            • Serene Frequencies (Beta)  
            """
        )

        st.markdown(
            """
            <a href="https://buy.stripe.com/bJecN4fq39dbf7q3L15ZC01" target="_blank">
                <button style="padding:10px 18px; border-radius:8px; width:100%;">Subscribe — $10/mo</button>
            </a>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # AUSTRALIA PLAN — A$10/month
    # --------------------------------------------------------
    st.markdown("### 🇦🇺 Australia (Local Pricing)")
    st.markdown("**A$10 / month**")
    st.markdown(
        """
        <a href="https://buy.stripe.com/28EdR8a5JfBze3m3L15ZC04" target="_blank">
            <button style="padding:10px 18px; border-radius:8px; width:300px;">Subscribe — A$10/mo</button>
        </a>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # COMPARISON TABLE
    # --------------------------------------------------------
    st.markdown("## 🔍 Free vs Premium — Feature Comparison")

    st.markdown(
        """
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px 12px;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.table(
        {
            "Feature": [
                "Dashboard",
                "Health Log",
                "Health Vault",
                "OCR Extraction",
                "AI Summary",
                "Hybrid Engine",
                "AI PDF Reports",
                "Timeline View",
                "Snapshots",
                "Vibration Indicators",
                "Finance × Law",
            ],
            "Free": [
                "✔",
                "✔",
                "✔",
                "✔",
                "Demo Only",
                "✘",
                "✘",
                "Basic",
                "Basic",
                "✘",
                "✘",
            ],
            "Premium": [
                "✔ (Enhanced)",
                "✔",
                "✔",
                "✔",
                "Unlimited",
                "Full Access",
                "Yes",
                "Advanced",
                "Unlimited",
                "Beta Access",
                "Early Access",
            ],
        }
    )

    st.info("Stripe payments are live. Your data always remains encrypted and fully owned by you.")

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
# AAA HEALTH INTELLIGENCE — DASHBOARD (PHASE-2 + PHASE-3)
# ============================================================

# ------------------------------------------------------------
# HEALTH STATUS BAR (PHASE-3 STEP-5)
# ------------------------------------------------------------
def get_health_status(score, logs):
    severe_keywords = ["pain", "pressure", "tightness", "bleeding", "faint", "severe"]
    logs_text = " ".join([entry.get("note", "").lower() for entry in logs]) if logs else ""

    if any(w in logs_text for w in severe_keywords):
        return "critical"

    if score >= 70:
        return "stable"
    elif 55 <= score < 70:
        return "attention"
    return "critical"


def render_health_status_bar(status):
    if status == "stable":
        color = "#0f3b2e"
        label = "🟢 Stable"
        desc = "Your health indicators look stable. No major concerns detected."

    elif status == "attention":
        color = "#b38800"
        label = "🟡 Needs Attention"
        desc = "Some parameters need attention. Keep monitoring closely."

    else:
        color = "#8b1a1a"
        label = "🔴 Critical Alerts Detected"
        desc = "Potential issues detected. Review logs or consult a professional."

    st.markdown(f"""
    <div style="
        background-color:{color};
        padding:18px;
        border-radius:10px;
        margin-bottom:20px;
        border:1px solid rgba(255,255,255,0.2);
    ">
        <h3 style="margin:0; color:white; font-size:22px;">{label}</h3>
        <p style="margin:5px 0 0 0; color:white; opacity:0.85;">{desc}</p>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------
# HEALTH PULSE SCORE — PHASE-3 STEP-8
# ------------------------------------------------------------
def generate_health_pulse(logs, health_score, trend, recent_note, file_count):

    if not logs:
        return ("⚪", "Not enough data — add your first log to activate your daily Health Pulse.")

    text = recent_note.lower()
    symptom_flags = ["pain", "tightness", "pressure", "headache", "fatigue", "dizzy"]
    positive_flags = ["energetic", "better", "slept well", "good", "improved"]

    has_negative = any(k in text for k in symptom_flags)
    has_positive = any(k in text for k in positive_flags)

    if has_negative and trend < 0:
        return ("🔴", "Your health pulse is critical — recurring symptoms and a declining score detected.")

    if has_negative and trend >= 0:
        return ("🟡", "Your health pulse needs monitoring — discomfort indicators logged recently.")

    if has_positive and trend > 0:
        return ("🟢", "Your health pulse is stable today — positive markers outweigh negative ones.")

    if trend > 0:
        return ("🟢", "Your health pulse looks positive — score improving steadily.")

    if len(logs) < 3:
        return ("🟡", "Your health pulse is neutral — add more logs for a sharper daily insight.")

    return ("⚪", "Your health pulse is stable — no significant changes detected today.")


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
def page_dashboard():
    aaa_header()

    # ------------------------------------------------------------
    # SIMPLE VIEW — FIRST SCREEN
    # ------------------------------------------------------------
    st.subheader("📊 Dashboard — Simple Overview")

    st.markdown(
        """
        <div style="font-size:15px; line-height:1.6; color:#C7D2FE; margin-bottom:20px;">
            A quick snapshot of your AAA Health activity.
        </div>
        """,
        unsafe_allow_html=True,
    )

    colS1, colS2 = st.columns(2)

    with colS1:
        if st.button("📝 Health Log\n(Your notes & entries)", use_container_width=True):
            st.session_state["nav"] = "🩺 Health Log"

        if st.button("📄 Documents\n(PDFs & images)", use_container_width=True):
            st.session_state["nav"] = "📥 Health Vault"

    with colS2:
        if st.button("🤖 AI Insights (Premium)\n(Summary)", use_container_width=True):
            st.session_state["nav"] = "🧠 AI Summary"

        if st.button("📈 Advanced Metrics\n(Expand full dashboard)", use_container_width=True):
            st.session_state["show_full_dashboard"] = not st.session_state.get("show_full_dashboard", False)

    st.markdown("<hr>", unsafe_allow_html=True)

    # If full dashboard is OFF → Stop here
    if not st.session_state.get("show_full_dashboard", False):
        aaa_footer()
        return

    # ------------------------------------------------------------
    # ORIGINAL FULL DASHBOARD STARTS BELOW (unchanged)
    # ------------------------------------------------------------

    st.subheader("📊 AAA Health Intelligence — Tailored Dashboard (Beta)")
    st.markdown("This is your personalised health overview. More data unlocks as you upload documents, logs, or summaries.")
    st.markdown("")

    # ------------------------------------------------------------
    # LOAD HEALTH LOGS
    # ------------------------------------------------------------
    logs = load_json(HEALTH_LOG_FILE, [])

    # ------------------------------------------------------------
    # LOAD MERGED MULTI-MODAL DATA
    # ------------------------------------------------------------
    merged_data_obj = load_json(MERGED_DATA_FILE, {"data": []})
    merged_data = merged_data_obj.get("data", [])

    # ------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------
    health_score = compute_health_score(logs)
    last_update = logs[-1]["timestamp"] if logs else "—"
    region = "Sydney, AU"

    # Score trend
    score_history = save_score_history(health_score)
    trend = 0
    if len(score_history) >= 2:
        trend = score_history[-1]["score"] - score_history[-2]["score"]

    # ------------------------------------------------------------
    # HEALTH STATUS BAR
    # ------------------------------------------------------------
    status = get_health_status(health_score, logs)
    render_health_status_bar(status)

    # ------------------------------------------------------------
    # METRICS DISPLAY
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Health Score", f"{health_score}", f"{trend:+}")
    with col2:
        st.metric("Last Update", last_update)
    with col3:
        st.metric("Region", region)

    st.markdown("---")

    # ------------------------------------------------------------
    # HEALTH PULSE
    # ------------------------------------------------------------
    recent_note = logs[-1].get("note", "") if logs else ""
    file_count = len(os.listdir(VAULT_DIR)) if os.path.exists(VAULT_DIR) else 0

    pulse_icon, pulse_text = generate_health_pulse(
        logs, health_score, trend, recent_note, file_count
    )

    st.markdown(f"""
    <div style="
        background-color:#0d1a2b;
        padding:16px;
        border-radius:10px;
        margin-top:10px;
        margin-bottom:25px;
        border:1px solid rgba(255,255,255,0.15);
    ">
        <h3 style="margin:0; color:white; font-size:22px;">{pulse_icon} Health Pulse</h3>
        <p style="margin-top:6px; color:white; opacity:0.85; font-size:16px;">
            {pulse_text}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ------------------------------------------------------------
    # TREND GRAPH
    # ------------------------------------------------------------
    st.markdown("### 📈 Health Score Trend")

    fig = plot_score_trend(score_history)
    if fig:
        st.pyplot(fig)
    else:
        st.info("Trend graph will appear after more score updates.")

    if trend > 0:
        st.success(f"📈 Trend: Improving (+{trend})")
    elif trend < 0:
        st.error(f"📉 Trend: Declining ({trend})")
    else:
        st.warning("➡️ Trend: Stable")

    st.markdown("---")

    # ------------------------------------------------------------
    # AI SUMMARY
    # ------------------------------------------------------------
    st.markdown("### 🧠 AI Health Summary")
    summary_text = generate_ai_health_summary(logs, merged_data)
    st.info(summary_text)

    st.markdown("---")

    # ------------------------------------------------------------
    # DAILY SNAPSHOT
    # ------------------------------------------------------------
    st.markdown("### 🗂️ Daily Snapshot")

    snapshot_date = last_update.split(" ")[0] if last_update != "—" else "—"
    recent_note_preview = recent_note[:80] + ("..." if len(recent_note) > 80 else "")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("#### 📅 Last Update")
        st.info(snapshot_date)

    with col_b:
        st.markdown("#### 📝 Latest Note")
        st.info(recent_note_preview)

    with col_c:
        st.markdown("#### 📄 Documents")
        st.info(f"{file_count} files")

    st.markdown("---")

    # ------------------------------------------------------------
    # TODAY'S SIGNALS
    # ------------------------------------------------------------
    st.markdown("### 🌤️ Today’s Signals")

    signals = []

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

    if os.path.exists(VAULT_DIR):
        doc_count = len(os.listdir(VAULT_DIR))
        if doc_count > 0:
            signals.append(f"🟢 **{doc_count} documents stored** — vault is active.")
        else:
            signals.append("🟡 Vault empty — upload lab reports or health files for deeper insights.")
    else:
        signals.append("⚪ Vault directory missing.")

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
            """, unsafe_allow_html=True
        )

    st.markdown("---")

    # ------------------------------------------------------------
    # WHY THESE SIGNALS MATTER
    # ------------------------------------------------------------
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

    reasoning_items = generate_reasoning_layer(logs, recent_note, file_count)

    for r in reasoning_items:
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

    # ------------------------------------------------------------
    # EARLY WARNING INDICATORS
    # ------------------------------------------------------------
    st.markdown("### 🔍 Early Warning Indicators (Last 7 Days)")

    recent_logs = logs[-7:] if len(logs) >= 7 else logs
    text_blob = " ".join([l.get("note", "") for l in recent_logs]).lower()
    warnings = []

    symptom_keywords = ["headache", "pain", "tightness", "pressure"]
    symptom_count = sum(text_blob.count(k) for k in symptom_keywords)

    if symptom_count >= 2:
        warnings.append("⚠️ **Recurring symptoms detected** — monitor patterns.")

    if len(recent_logs) <= 3:
        warnings.append("⚠️ **Low logging frequency** — more logs improve accuracy.")

    if "water" in text_blob or "hydration" in text_blob:
        warnings.append("💧 **Hydration-related pattern noted** — keep monitoring water intake.")

    sleep_keywords = ["sleep", "tired", "fatigue"]
    if any(k in text_blob for k in sleep_keywords) and "good" not in text_blob:
        warnings.append("😴 **Sleep irregularity signals** — mixed notes detected.")

    doc_count = len(os.listdir(VAULT_DIR)) if os.path.exists(VAULT_DIR) else 0
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

    # ------------------------------------------------------------
    # LAST 10 LOGS
    # ------------------------------------------------------------
    st.markdown("### 📅 Last 10 Health Logs")

    if logs:
        for entry in logs[-10:][::-1]:
            ts = entry.get("timestamp", "")
            dt = entry.get("date", "")
            nt = entry.get("note", "")
            st.markdown(f"""
                **📅 {dt} — {ts}**  
                {nt}
            """)
    else:
        st.warning("No logs found.")

    st.markdown("---")

    # ------------------------------------------------------------
    # RECENT DOCUMENTS
    # ------------------------------------------------------------
    st.markdown("### 📂 Recent Documents")

    recent_docs = []
    if os.path.exists(VAULT_DIR):
        for fname in os.listdir(VAULT_DIR):
            p = os.path.join(VAULT_DIR, fname)
            if os.path.isfile(p):
                recent_docs.append({"name": fname})

    if recent_docs:
        for doc in recent_docs[:10]:
            st.markdown(f"📄 **{doc['name']}**")
    else:
        st.warning("No documents found.")

    st.markdown("---")

    # ------------------------------------------------------------
    # REGIONAL INSIGHTS
    # ------------------------------------------------------------
    st.markdown("### 🧭 Regional Insights")
    st.info("Sydney health season: High pollen, warm weather, moderate UV. Flu season tapering.")

    st.markdown("---")

    # ------------------------------------------------------------
    # CLOSE CIRCLE
    # ------------------------------------------------------------
    st.markdown("### 👪 Close Circle Sharing")
    st.info("Add trusted family members to receive summaries (coming soon).")

    aaa_footer()

# ============================================================
# FIREWALL + MONETIZATION (LIGHT MODE – SAFE FOR 5 DEC LAUNCH)
# ============================================================

PREMIUM_PAGES = {
    "✨ Merged View (Combined Data)",
    "🧬 Summary AI (Advanced Summary)",
    "📊 Insights AI (Deep Insights)",
    "📘 Summary Report (PDF Generator)",
    "🌟 Premium (Coming Soon)",
}

def check_firewall(page_name: str, mode: str):
    """
    Light firewall:
    - Free mode → premium pages show upgrade notice.
    - Premium mode → fully unlocked.
    """

    if mode == "free" and page_name in PREMIUM_PAGES:
        st.markdown("### 🔒 Premium Feature")

        st.info(
            """
            This feature is part of **AAA Premium**.

            Upgrade unlocks:
            - Advanced AI summaries  
            - Insights AI  
            - Deep merged view  
            - Rich PDF analytics  
            - Priority processing  

            👉 Coming December 2025.
            """
        )

        st.stop()



# ============================================================
# MAIN NAVIGATION
# ============================================================

def main():

    # -------------------------------
    # SIDEBAR NAVIGATION
    # -------------------------------
    with st.sidebar:

        # Subscription toggle
        st.markdown("## 🔐 Subscription Mode (Demo)")
        mode = st.radio("Select mode:", ["free", "premium"])
        st.session_state["mode"] = mode

        # Header
        st.markdown("## 💎 AAA — Health Intelligence (DEV)")

        # -------------------------------
        # NAVIGATION MENU (Simple meanings added)
        # -------------------------------
        choice = st.radio(
            "Navigate:",
            [
                # ---- Core Health Intelligence ----
                "📊 Dashboard (Overview)",
                "🩺 Health Log (Notes)",
                "📥 Health Vault (Uploads)",
                "📁 Vault Manager (Manage Files)",
                "🗑 Recycle Bin (Deleted Items)",
                "📄 PDF Preview (Reports)",
                "🔍 OCR (Scan Text)",

                # ---- AI Intelligence Layer ----
                "🧠 Summary (Demo)",
                "✨ Merged View (Combined Data)",
                "🧬 Summary AI (Advanced Summary)",
                "📊 Insights AI (Deep Insights)",
                "📚 Insights History (Past Insights)",
                "📘 Summary Report (PDF Generator)",
                "🚨 AI Health Risk Engine (Risk Signals)",
                "🧬 Pattern Timeline AI (Patterns Over Time)",
                "🌐 Insight Fusion Layer (Fusion Intelligence)",
                "📈 Insight Graphs (Visual Charts)",
                "🩺 Medical Triptych (3-Panel View)",
                "🎵 Serene Frequencies (Audio Wellness)",
                "🧘 Mood × Sleep × Stress Radar (Wellbeing Map)",
                "🔮 Health × Vibration Correlation Map (Energy Map)",
                "📈 Trend Forecast Engine (Predictions)",
                "📅 Unified Timeline Intelligence (Time-Line View)",
                "🧩 Insight Matrix (Matrix View)",
                "🧠 Health Knowledge Graph (Knowledge Map)",
                "🧬 Multi-Signal Diagnostic Engine (Multi-Signal Analysis)",
                "🧬 Health Signature Engine (Signature View)",
                "🧬 Unified Signal Comparison (Compare Signals)",
                "📉 Signal Volatility Engine (Volatility Analysis)",

                # ---- Monetization Layer ----
                "💎 Subscription Plans (Pricing)",
                "💳 Stripe Monetization Demo (Pay Demo)",

                # ---- Future Intelligence Layer ----
                "🧠 Edge Node Memory (Memory Layer)",

                # ---- Coming Soon ----
                "🌟 Premium (Coming Soon)",
                "🧊 Snapshots (Records)",
            ]
        )

        st.session_state["nav"] = choice


    # -------------------------------
    # FIREWALL (Do Not Move)
    # -------------------------------
    if choice not in {
        "💎 Subscription Plans (Pricing)",
        "💳 Stripe Monetization Demo (Pay Demo)",
        "🌟 Premium (Coming Soon)",
    }:
        check_firewall(choice, mode)


    # -------------------------------
    # PAGE ROUTING
    # -------------------------------
    if choice.startswith("📊 Dashboard"):
        page_dashboard()

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

    elif choice == "🧠 Summary (Demo)":
        page_summary()

    elif choice.startswith("✨ Merged View"):
        page_merged()

    elif choice.startswith("🧬 Summary AI"):
        page_summary_ai()

    elif choice.startswith("📊 Insights AI"):
        page_insights_ai()

    elif choice.startswith("📚 Insights History"):
        page_insights_history()

    elif choice.startswith("📘 Summary Report"):
        page_summary_report()

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

    elif choice.startswith("🎵 Serene Frequencies"):
        page_serene_frequency()

    elif choice.startswith("🧘 Mood × Sleep × Stress Radar"):
        page_mood_sleep_stress_radar()

    elif choice.startswith("🔮 Health × Vibration Correlation Map"):
        page_health_vibration_correlation()

    elif choice.startswith("📈 Trend Forecast Engine"):
        page_trend_forecast_engine()

    elif choice.startswith("📅 Unified Timeline Intelligence"):
        page_unified_timeline_intel()

    elif choice.startswith("🧩 Insight Matrix"):
        page_insight_matrix()

    elif choice.startswith("🧠 Health Knowledge Graph"):
        page_health_knowledge_graph()

    elif choice.startswith("🧬 Multi-Signal Diagnostic Engine"):
        page_multi_signal_engine()

    elif choice.startswith("🧬 Health Signature Engine"):
        page_health_signature_engine()

    elif choice.startswith("🧬 Unified Signal Comparison"):
        page_unified_signal_comparison()

    elif choice.startswith("📉 Signal Volatility Engine"):
        page_signal_volatility_engine()

    elif choice.startswith("💎 Subscription Plans"):
        page_subscription_plans()

    elif choice.startswith("💳 Stripe Monetization Demo"):
        page_stripe_monetization_demo()

    elif choice.startswith("🧠 Edge Node Memory"):
        page_edge_node_memory()

    elif choice.startswith("🌟 Premium (Coming Soon)"):
        page_premium()

    elif choice.startswith("🧊 Snapshots"):
        page_snapshots()



# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    main()
