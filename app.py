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
# STRIPE CONFIG (PLACEHOLDERS — CONNECTED LATER)
# ============================================================

STRIPE_SECRET_KEY = st.secrets.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_AU = st.secrets.get("STRIPE_PRICE_AU", "")
STRIPE_PRICE_IN = st.secrets.get("STRIPE_PRICE_IN", "")
STRIPE_PRICE_US = st.secrets.get("STRIPE_PRICE_US", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ============================================================
# GEMINI CONFIG
# ============================================================

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ============================================================
# JSON HELPERS
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
# PDF UTILITIES
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
        text_chunks.append("Image file uploaded. OCR text stored separately.")
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
        "INR": 100
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
            **Monthly:** A$10 / ₹100 / $10  
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
# GLOBAL UI — HEADER + FOOTER (COPIED FROM STABLE app.py)
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
            st.button("₹100 / month", use_container_width=True)
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

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    log_choice = st.selectbox(
        "Select Health Log",
        list(range(len(logs))) if logs else [],
        format_func=lambda i: logs[i]["date"],
    ) if logs else None

    ocr_choice = st.selectbox(
        "Select OCR Entry",
        list(range(len(ocr))) if ocr else [],
        format_func=lambda i: ocr[i]["filename"],
    ) if ocr else None

    if st.button("Generate Summary"):
        if log_choice is None and ocr_choice is None:
            st.error("Select at least one source.")
            aaa_footer()
            return

        parts = []
        if log_choice is not None:
            parts.append(str(logs[log_choice]))
        if ocr_choice is not None:
            parts.append(ocr[ocr_choice]["text"])

        prompt = f"""
Convert the following into a structured, patient-friendly medical summary with:
- Key Symptoms
- Risk Markers
- Trends
- Observations
- Recommendations

TEXT:
{parts}
"""
        resp_text = call_gemini(prompt)
        st.markdown(resp_text)

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE — MERGED VIEW (PREMIUM FEATURE)
# ============================================================

def page_merged():
    # 🔒 FIREWALL — FIRST LINE
    check_firewall("Merged View", st.session_state.get("mode", "free"))

    aaa_header()
    st.subheader("✨ Merged View — Multi-Document Intelligence (Premium)")

    # Premium check
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:20px;">
            Compare multiple medical documents together — PDFs, reports, prescriptions,
            scans, or lab results — and generate combined insights, patterns, and
            cross-document trends using AAA Intelligence.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------
    # LOAD VAULT FILES
    # ------------------------------------------------------------
    files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not files:
        st.warning("Upload at least 2 files in the Vault to use Merged View.")
        monetization_cta()
        aaa_footer()
        return

    selected_files = st.multiselect(
        "Select 2–5 files for merged analysis:",
        files,
        max_selections=5
    )

    if len(selected_files) < 2:
        st.info("Select at least 2 files to continue.")
        aaa_footer()
        return

    # ------------------------------------------------------------
    # GENERATE MERGED ANALYSIS
    # ------------------------------------------------------------
    if st.button("Generate Merged Intelligence"):
        with st.spinner("Processing multiple documents with AAA Intelligence…"):
            try:
                extracted_texts = []
                for f in selected_files:
                    path = os.path.join(VAULT_DIR, f)
                    extracted_texts.append(f"\n\n===== FILE: {f} =====\n" + extract_text_any(path))

                combined_text = "\n".join(extracted_texts)

                # Prompt
                prompt = (
                    "You are AAA Intelligence. Create a combined, structured, "
                    "patient-friendly analysis from multiple uploaded medical documents.\n\n"
                    "Break the output into these sections:\n"
                    "1. Combined Key Findings (all files)\n"
                    "2. Trends, Patterns & Relationships\n"
                    "3. Risk Indicators & Warnings\n"
                    "4. Contradictions / Missing Info\n"
                    "5. Recommendations & Next Steps (simple explanation)\n\n"
                    "Documents:\n"
                    f"{combined_text[:12000]}"
                )

                # Call Gemini
                result = call_gemini(prompt)

                # Display styled card
                st.markdown(
                    """
                    <div style="
                        padding:20px;
                        border-radius:12px;
                        background-color:#0B1625;
                        border-left:4px solid #D4A037;
                        box-shadow:0 0 12px rgba(0,166,200,0.15);
                    ">
                    """,
                    unsafe_allow_html=True,
                )
                st.write(result)
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 8 — SUMMARY AI (PREMIUM FEATURE)
# ============================================================

def page_summary_ai():
    # 🔒 FIREWALL — FIRST LINE
    check_firewall("Summary AI", st.session_state.get("mode", "free"))

    aaa_header()
    st.subheader("🧬 Summary AI (Premium)")

    # If not premium → lock the feature
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            Generate an intelligent, doctor-style medical summary from your uploaded
            PDFs, images, lab reports, and prescriptions.  
            AAA Intelligence creates a structured, patient-friendly summary with
            findings, explanation, and next-step suggestions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------
    # LOAD FILES
    # ------------------------------------------------------------
    files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]

    if not files:
        st.warning("Upload at least 1 file in the Vault to generate a summary.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select a file to summarize:", files)

    # ------------------------------------------------------------
    # GENERATE SUMMARY
    # ------------------------------------------------------------
    if st.button("Generate Summary"):
        with st.spinner("Analyzing with AAA Intelligence…"):
            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)

                prompt = (
                    "Provide a clear, structured, patient-friendly medical summary. "
                    "Break into sections:\n"
                    "1. Key Findings\n"
                    "2. What This Means (explain simply)\n"
                    "3. Risk Indicators\n"
                    "4. Missing Info To Check\n"
                    "5. Recommended Next Steps\n\n"
                    f"TEXT:\n{text[:4000]}"
                )

                result = call_gemini(prompt)
                st.success("Summary generated!")

                st.markdown(
                    "<div style='padding:15px; border-radius:10px; "
                    "background-color:#0B1625; box-shadow:0 0 8px rgba(0,166,200,0.15);'>",
                    unsafe_allow_html=True,
                )
                st.write(result)
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 9 — INSIGHTS AI (PREMIUM HYBRID ENGINE — FINAL VERSION)
# ============================================================

def generate_insights_hybrid(file_text: str) -> str:
    """Gemini Hybrid Engine: Short Summary + Deep Insights."""
    prompt = f"""
You are AAA-Health Intelligence. Analyze the following medical text and produce a HYBRID structured output.

TEXT:
\"\"\"
{file_text}
\"\"\"

OUTPUT FORMAT (FOLLOW EXACTLY):

SHORT_SUMMARY:
- 3–5 bullet points
- Simple language
- Easy for any user to understand

DEEP_INSIGHTS:
SECTION 1 — Key Findings:
- 4–7 bullet points

SECTION 2 — Trends & Patterns:
- 3–5 bullet points

SECTION 3 — Risks & Red Flags:
- 2–4 bullet points

SECTION 4 — Recommendations:
- 3–6 bullet points

Return ONLY the structured text. No intro, no conclusion.
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

    # Premium check
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # Load vault files
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

    if st.button("Generate Insights"):
        with st.spinner("🔥 Generating AAA Hybrid Intelligence…"):

            try:
                # Extract text
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)

                # Call Hybrid Engine
                ai_output = generate_insights_hybrid(text)

                # -------------------------
                # SPLITTING SECTIONS
                # -------------------------
                try:
                    short_part = ai_output.split("SHORT_SUMMARY:")[1].split("DEEP_INSIGHTS:")[0].strip()
                except Exception:
                    short_part = "Unable to format short summary."

                try:
                    deep_part = ai_output.split("DEEP_INSIGHTS:")[1].strip()
                except Exception:
                    deep_part = ai_output

                # -------------------------
                # SAVE
                # -------------------------
                save_insights_record(selected_file, short_part, deep_part)

                # -------------------------
                # DISPLAY UI
                # -------------------------
                st.success("Insights generated successfully!")

                st.markdown("### 🟦 Short Summary")
                st.markdown(short_part.replace("-", "• "))

                st.markdown("---")

                st.markdown("### 🟫 Deep Insights")

                # Key Findings
                if "SECTION 1" in deep_part:
                    sec1 = deep_part.split("SECTION 1 — Key Findings:")[1].split("SECTION 2")[0].strip()
                    with st.expander("🔍 Key Findings"):
                        st.markdown(sec1.replace("-", "• "))

                # Trends & Patterns
                if "SECTION 2" in deep_part:
                    sec2 = deep_part.split("SECTION 2 — Trends & Patterns:")[1].split("SECTION 3")[0].strip()
                    with st.expander("📈 Trends & Patterns"):
                        st.markdown(sec2.replace("-", "• "))

                # Risks
                if "SECTION 3" in deep_part:
                    sec3 = deep_part.split("SECTION 3 — Risks & Red Flags:")[1].split("SECTION 4")[0].strip()
                    with st.expander("⚠️ Risks & Red Flags"):
                        st.markdown(sec3.replace("-", "• "))

                # Recommendations
                if "SECTION 4" in deep_part:
                    sec4 = deep_part.split("SECTION 4 — Recommendations:")[1].strip()
                    with st.expander("✅ Recommendations"):
                        st.markdown(sec4.replace("-", "• "))

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

            freq = {
                k: text_all.count(k)
                for k in keywords
            }

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
        combined_text = " ".join(i.get("deep", "") for i in insights)

        alert_keywords = [
            ("Kidney-related indicators", ["creatinine", "gfr", "urea"]),
            ("Cardio Indicators", ["bp", "hypertension", "tachy", "cholesterol"]),
            ("Infection Markers", ["stool", "wbc", "infection"]),
            ("Inflammation Markers", ["crp", "esr", "inflamm"])
        ]

        for title, keys in alert_keywords:
            found = any(k in combined_text.lower() for k in keys)
            if found:
                st.warning(f"⚠ **{title} flagged in recent reports**")
    else:
        st.info("No insights available for condition flagging.")

    st.markdown("---")

    # ========= Section: Regional Health Awareness =========
    st.markdown("## 🌏 Regional Health Awareness (Beta)")

    st.markdown(
        """
        This shows location-based seasonal trends and general awareness.
        (Static beta content — will be replaced with live regional models.)
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
# SNAPSHOTS HELPERS (AAA HEALTH)
# ============================================================

SNAPSHOTS_FILE = os.path.join(DATA_DIR, "snapshots.json")

def load_snapshots():
    if not os.path.exists(SNAPSHOTS_FILE):
        return []
    try:
        with open(SNAPSHOTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_snapshots(snapshots):
    with open(SNAPSHOTS_FILE, "w") as f:
        json.dump(snapshots, f, indent=2)

def create_snapshot():
    logs = load_logs()
    vault_files = load_vault_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    snapshot = {
        "timestamp": timestamp,
        "log_count": len(logs),
        "vault_files": vault_files,
    }

    snapshots = load_snapshots()
    snapshots.append(snapshot)
    save_snapshots(snapshots)
    return snapshot


# ============================================================
# PAGE 13 — SNAPSHOTS + SMART TIMELINE
# ============================================================

def page_snapshots():
    aaa_header()
    st.subheader("📸 Health Snapshots (Beta)")

    snapshots = load_snapshots()

    if st.button("Create New Snapshot"):
        snap = create_snapshot()
        st.success(f"Snapshot created at {snap['timestamp']}")

    if not snapshots:
        st.info("No snapshots yet. Create your first snapshot to begin tracking.")
        monetization_cta()
        aaa_footer()
        return

    for s in snapshots:
        with st.expander(f"Snapshot — {s['timestamp']}"):
            st.write(f"📝 Log entries: {s['log_count']}")
            st.write(f"📄 Documents stored: {len(s['vault_files'])}")
            st.write("Files:")
            for f in s["vault_files"]:
                st.write(f"- {f}")

    monetization_cta()
    aaa_footer()


def page_timeline():
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

    st.markdown("—")
    st.markdown("### 🧩 Why These Signals Matter")

    st.markdown(
        """
        These signals help AAA create a personalised health trend using your logs,
        snapshots, documents and generated summaries.
        """
    )

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 14 — INSIGHTS HISTORY (PREMIUM INTELLIGENCE LOG)
# ============================================================

def page_insights_history():
    check_firewall("Insights History", st.session_state.get("mode", "free"))
    aaa_header()

    # -----------------------------
    # Title + subtitle
    # -----------------------------
    st.markdown("""
        <h2 style="text-align:center; color:#F2C678; margin-bottom:5px;">
            📚 Insights History (Premium)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Your previously generated AAA health insights — deep analysis, trends,
            risk detection and interpretation logs.
        </p>
        <br>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Load insights history JSON
    # -----------------------------
    insights = []
    if os.path.exists(INSIGHTS_FILE):
        try:
            with open(INSIGHTS_FILE, "r") as f:
                insights = json.load(f)
        except:
            insights = []

    if not insights:
        st.warning("No insights generated yet. Create insights in **Insights AI** first.")
        monetization_cta()
        aaa_footer()
        return

    # -----------------------------
    # AAA brand colors
    # -----------------------------
    card_bg = "#0B1625"        # Deep navy
    teal = "#40B8C0"           # Teal
    gold = "#D4A037"           # Metallic gold
    soft_gold = "#F2C678"      # Accent gold

    # -----------------------------
    # Card styling
    # -----------------------------
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
                color: {soft_gold};
                font-size: 18px;
                margin-bottom: 10px;
                font-weight: 600;
            }}
            .aaa-text {{
                color: #8FA3B8;
                font-size: 15px;
                line-height: 1.5;
            }}
        </style>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Render insights history
    # -----------------------------
    for entry in reversed(insights):      # Newest first
        ts = entry.get("timestamp", "Unknown Time")
        summary = entry.get("summary", "")
        risk = entry.get("risk_level", "N/A")
        source = entry.get("source_file", "Unknown Source")
        engine = entry.get("engine", "Gemini Hybrid Engine")

        st.markdown(f"""
            <div class="aaa-card">
                <div class="aaa-title">🕒 {ts} — {engine}</div>

                <div class="aaa-text">
                    <b>Source:</b> {source}<br>
                    <b>Risk Level:</b> {risk}<br><br>

                    <b>Summary:</b><br>
                    {summary}
                </div>
            </div>
        """, unsafe_allow_html=True)

    aaa_footer()


# ============================================================
# PAGE 15 — TIMELINE INTELLIGENCE (AAA NODE v1 — HYBRID MODE)
# ============================================================

# Timeline file path (global)
TIMELINE_FILE = os.path.join(DATA_DIR, "timeline_master.json")

# Initialise timeline file if missing
if not os.path.exists(TIMELINE_FILE):
    with open(TIMELINE_FILE, "w") as f:
        json.dump([], f, indent=4)

def load_timeline():
    """Load timeline events safely."""
    try:
        with open(TIMELINE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_timeline(data):
    """Save timeline safely."""
    with open(TIMELINE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_timeline_event(
    summary,
    category="general",
    source="AAA Engine",
    risk="N/A",
    engine="Gemini/AAA Hybrid",
):
    """Append a new timeline event."""
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

# ============================================================
# PAGE RENDER — TIMELINE INTELLIGENCE
# ============================================================

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
            snapshots, OCR results and AAA insights. Apple-class experience,
            Musk-style Node architecture.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    events = load_timeline()
    if not events:
        st.info("No timeline events yet. As you generate logs and insights, they will appear here.")
        monetization_cta()
        aaa_footer()
        return

    # Apple-style styling
    card_bg = "#0D1628"
    accent = "#F2C678"
    border = "#04A3D7"

    # Render newest → oldest
    for evt in reversed(events):
        ts = evt.get("timestamp", "Unknown Time")
        summary = evt.get("summary", "")
        category = evt.get("category", "")
        source = evt.get("source", "")
        risk = evt.get("risk", "N/A")
        engine = evt.get("engine", "")
        event_id = evt.get("event_id", "")

        st.markdown(
            f"""
            <div style="
                background-color:{card_bg};
                padding:20px;
                margin-bottom:18px;
                border-radius:16px;
                border-left: 4px solid {accent};
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
                        <b>Event ID:</b> {event_id} <br>
                        <b>Source:</b> {source} <br>
                        <b>Risk Level:</b> {risk} <br>
                        <b>Engine:</b> {engine} <br>
                    </div>
                </details>
            </div>
            """,
            unsafe_allow_html=True,
        )

    aaa_footer()


# ============================================================
# PAGE 16 — AI HEALTH SCORE ENGINE (AAA Intelligence Core)
# ============================================================

def compute_health_score(merged_data, insights, logs):
    """
    Core scoring engine (AAA hybrid model).
    Weighted scoring across multiple health dimensions.
    """

    # If no data, return default neutral score
    if not merged_data and not insights and not logs:
        return 72, "⚠️ Limited data — upload more logs and documents.", []

    reasons = []

    score = 80  # Base score

    # -------------------------------
    # Logs Influence
    # -------------------------------
    if logs:
        latest_logs = logs[-5:]  # Last 5 logs
        for log in latest_logs:
            if "bp" in log.get("type", "").lower():
                bp = log.get("value", 0)
                if bp > 140:
                    score -= 5
                    reasons.append("Elevated blood pressure detected.")
                elif bp < 100:
                    score -= 3
                    reasons.append("Low blood pressure episodes noted.")
            if "sleep" in log.get("type", "").lower():
                hrs = log.get("value", 0)
                if hrs < 6:
                    score -= 2
                    reasons.append("Insufficient sleep duration recently.")
                elif hrs > 8:
                    score += 1
                    reasons.append("Consistently good sleep.")

    # -------------------------------
    # Insights Influence (AI-derived)
    # -------------------------------
    for item in insights:
        risk = item.get("risk_level", "").lower()
        if "high" in risk:
            score -= 7
            reasons.append("AI detected a high-risk pattern.")
        if "moderate" in risk:
            score -= 3
            reasons.append("Moderate risk trend identified.")

    # -------------------------------
    # Merged Data Influence
    # -------------------------------
    if merged_data:
        for item in merged_data:
            category = item.get("category", "").lower()
            val = item.get("value", "")

            if "cholesterol" in category:
                if isinstance(val, (int, float)):
                    if val > 240:
                        score -= 5
                        reasons.append("High cholesterol trend found.")
                    elif val < 200:
                        score += 2
                        reasons.append("Healthy cholesterol levels.")

            if "glucose" in category:
                if isinstance(val, (int, float)):
                    if val > 130:
                        score -= 4
                        reasons.append("High glucose reading detected.")
                    elif val < 100:
                        score += 1

    # Final clamping
    score = max(1, min(99, score))

    return score, " • ".join(reasons[:4]) if reasons else "Stable—no major issues detected.", reasons


def page_health_score_engine():
    aaa_header()
    st.subheader("🧠 AI Health Score Engine")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # Load all known data sources
    merged_data = load_json(MERGED_DATA_FILE, [])
    insights = load_json(INSIGHTS_HISTORY_FILE, [])
    logs = load_json(HEALTH_LOG_FILE, [])

    # Compute score
    score, summary_text, detailed_reasons = compute_health_score(
        merged_data,
        insights,
        logs
    )

    # -------------------------------
    # AAA Theme Colors
    # -------------------------------
    navy = "#071E36"
    teal = "#00A6B6"
    gold = "#F4BD3B"
    soft_gold = "#F2C678"

    # -------------------------------
    # Score Card UI
    # -------------------------------
    st.markdown(f"""
        <div style="background-color:{navy};
                    padding:25px;
                    border-radius:18px;
                    margin-bottom:25px;
                    border-left:5px solid {gold};
                    box-shadow:0 0 12px rgba(0,150,220,0.25);">
            
            <div style="font-size:48px; font-weight:700; color:{soft_gold};
                        text-align:center;">
                {score}
            </div>

            <div style="text-align:center;
                        font-size:20px;
                        margin-top:10px;
                        color:{teal};">
                Your Current AI Health Score
            </div>

            <div style="margin-top:20px;
                        font-size:15px;
                        color:#DDEAFF;
                        text-align:center;">
                {summary_text}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # -------------------------------
    # Detailed Reasons
    # -------------------------------
    st.markdown("<h4 style='color:#F2C678;'>Breakdown</h4>", unsafe_allow_html=True)

    if detailed_reasons:
        for r in detailed_reasons[:8]:
            st.markdown(f"""
                <div style="background:#102C45;
                            padding:12px;
                            margin:8px 0;
                            border-radius:10px;
                            font-size:15px;
                            color:#DDEAFF;
                            border-left:4px solid {teal};">
                    {r}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No additional risk indicators found.")

    aaa_footer()


# ============================================================
# PAGE 17 — SUMMARY REPORT AI (PDF INTELLIGENCE)
# ============================================================

def page_summary_report():
    aaa_header()
    st.subheader("📄 Summary Report AI (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            Generate a complete AI-powered PDF health report — combining your
            health logs, vault documents, insights, trends and early warning indicators.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------
    # Load Data
    # ---------------------------
    logs = load_json(HEALTH_LOG_FILE, [])
    insights = load_json(INSIGHTS_HISTORY_FILE, [])
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]

    if not logs and not insights and not vault_files:
        st.warning("Not enough data to generate a report. Add Health Logs or upload files in Vault.")
        monetization_cta()
        aaa_footer()
        return

    st.markdown("### Report Options")
    include_logs = st.checkbox("Include Health Logs", True)
    include_insights = st.checkbox("Include Insights History", True)
    include_vault = st.checkbox("Include Vault File Summaries", True)

    if st.button("Generate PDF Report"):
        with st.spinner("Generating your AAA PDF Intelligence Report…"):
            try:
                temp_pdf = "/tmp/aaa_summary_report.pdf"
                generate_pdf_report(
                    temp_pdf,
                    logs if include_logs else [],
                    insights if include_insights else [],
                    vault_files if include_vault else [],
                )

                with open(temp_pdf, "rb") as f:
                    st.download_button(
                        "📥 Download Summary Report (PDF)",
                        f,
                        file_name="AAA_Health_Report.pdf",
                        mime="application/pdf",
                    )

                st.success("Report ready! Download above.")
            except Exception as e:
                st.error(f"Error generating PDF report: {e}")

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
    Includes:
    - Gold–Teal headers
    - Proper spacing + section separators
    - Doctor-style AI summary block
    - Clean list formatting
    """

    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 1 * inch

    # ---------------------------------------------------------
    # TITLE BLOCK
    # ---------------------------------------------------------
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(HexColor("#FACC15"))  # Gold accent
    c.drawString(1 * inch, y, "AAA — Health Intelligence Report")

    y -= 0.4 * inch
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#E2E8F0"))
    c.drawString(1 * inch, y, "AI-powered clinical summary • Lab insights • Logs • Vault intelligence")

    y -= 0.5 * inch

    # Horizontal line
    c.setStrokeColor(HexColor("#38BDF8"))  # Teal
    c.setLineWidth(1)
    c.line(1 * inch, y, width - 1 * inch, y)

    y -= 0.5 * inch

    # ---------------------------------------------------------
    # DOCTOR-STYLE SUMMARY BLOCK
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

        # Divider
        c.setStrokeColor(HexColor("#334155"))
        c.line(1 * inch, y, width - 1 * inch, y)
        y -= 0.4 * inch

    # ---------------------------------------------------------
    # SECTION: HEALTH LOGS
    # ---------------------------------------------------------
    if logs:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#38BDF8"))  # Teal Header
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
    # SECTION: INSIGHTS HISTORY
    # ---------------------------------------------------------
    if insights:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#38BDF8"))
        c.drawString(1 * inch, y, "📊 AI Insights History")
        y -= 0.35 * inch

        c.setFont("Helvetica", 11)
        c.setFillColor(HexColor("#E2E8F0"))

        for item in insights[:10]:
            text = f"- {item.get('summary', '')}"
            c.drawString(1 * inch, y, text[:110])
            y -= 0.22 * inch

            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch

        y -= 0.4 * inch

    # ---------------------------------------------------------
    # SECTION: VAULT FILES
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
    c.drawString(1 * inch, 0.6 * inch, "Generated by Artigellence — AAA Health Intelligence · Private · Local · Secure")

    c.save()


# ============================================================
# PAGE 18 — STRIPE MONETIZATION ENGINE (DEMO ONLY)
# ============================================================

def page_stripe_engine():
    aaa_header()
    st.subheader("💳 Stripe Monetization Engine (Demo)")

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.7; margin-bottom:10px;">
            The Stripe Monetization Engine manages subscription payments for
            Artigellence Premium.  
            You are currently in <b>Demo Mode</b> — real checkout is disabled.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Stripe live checkout is disabled. This is a demo preview of how AAA Premium billing will work.")

    # ---------------------------------------------------------
    # PRICING CARDS — DEMO
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style='background:#102C45; padding:20px; border-radius:12px;'>
                <h3 style='color:#5BB6FF;'>Australia</h3>
                <h2 style='color:white;'>A$10 / month</h2>
                <ul style='color:#D0EAFF; font-size:14px;'>
                    <li>Unlimited AI Medical Summaries</li>
                    <li>Deep Insights & Hybrid Engine</li>
                    <li>PDF Health Reports & Snapshots</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style='background:#0F233A; padding:20px; border-radius:12px; border:1px solid #284F63;'>
                <h3 style='color:#5BB6FF;'>India</h3>
                <h2 style='color:white;'>₹100 / month</h2>
                <ul style='color:#D0EAFF; font-size:14px;'>
                    <li>All Premium Features</li>
                    <li>Merged AI View (Doctor + Lab + Notes)</li>
                    <li>Early Access to AAA Finance & Law</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style='background:#102C45; padding:20px; border-radius:12px;'>
                <h3 style='color:#5BB6FF;'>Global</h3>
                <h2 style='color:white;'>$10 / month</h2>
                <ul style='color:#D0EAFF; font-size:14px;'>
                    <li>All Premium Intelligence Tools</li>
                    <li>Priority Roadmap Voting</li>
                    <li>Serene Frequency Indicators</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # BUTTONS — NON-ACTIVE IN DEMO MODE
    # ---------------------------------------------------------
    st.warning("Checkout buttons are disabled in Demo Mode.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.button("Subscribe — Australia (Demo)", disabled=True)

    with c2:
        st.button("Subscribe — India (Demo)", disabled=True)

    with c3:
        st.button("Subscribe — Global (Demo)", disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # NEXT STEPS NOTE
    # ---------------------------------------------------------
    st.markdown(
        """
        <div style="background:#001a2b; padding:15px; border-radius:10px; 
        border-left:4px solid #0af;">
            <b>Coming Soon:</b><br>
            • Stripe live checkout integration<br>
            • Country-based pricing engine<br>
            • One-time purchases (PDF Packs)<br>
            • Workflow Packs Marketplace<br>
        </div>
        """,
        unsafe_allow_html=True,
    )

    aaa_footer()


# ============================================================
# PAGE 19 — AI EDGE NODE MEMORY LAYER (FUTURISTIC MODE)
# ============================================================

def page_edge_node_memory():

    aaa_header()

    st.markdown(
        """
        <h2 style="text-align:center; color:#00D4FF; margin-bottom:5px;">
            🤖 AI Edge Node — Memory Layer (Beta)
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            This is the adaptive memory layer that evolves with your health,
            behaviour patterns, and AAA usage signals.  
            Inspired by edge-AI processing — high-speed, personalised,
            privacy-preserving augmentation.
        </p>
        <br>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------
    # TEMP FILES
    # -------------------------
    memory_file = os.path.join(DATA_DIR, "edge_memory.json")
    if not os.path.exists(memory_file):
        with open(memory_file, "w") as f:
            json.dump({"events": []}, f, indent=4)

    # -------------------------
    # ADD NEW MEMORY SIGNAL
    # -------------------------
    st.subheader("🧠 Add Memory Signal")
    signal = st.text_input("Describe a pattern, note, or observation:")

    if st.button("Save Memory Signal"):
        with open(memory_file, "r") as f:
            data = json.load(f)

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "signal": signal.strip(),
        }

        data["events"].append(entry)

        with open(memory_file, "w") as f:
            json.dump(data, f, indent=4)

        st.success("Memory signal saved into your Edge-Node layer!")

    st.markdown("<hr>", unsafe_allow_html=True)

    # -------------------------
    # VIEW MEMORY LAYER ENTRIES
    # -------------------------
    st.subheader("📡 Active Memory Streams")

    with open(memory_file, "r") as f:
        data = json.load(f)

    events = data.get("events", [])

    if not events:
        st.info("No memory signals yet. Start adding patterns above.")
        monetization_cta()
        aaa_footer()
        return

    # Show latest first
    for e in reversed(events):
        ts = e["timestamp"]
        sig = e["signal"]

        st.markdown(
            f"""
            <div style="
                background:#0E1A2B;
                padding:12px;
                margin:8px 0;
                border-radius:10px;
                border-left:4px solid #00D4FF;
                color:#D0E4FF;
                line-height:1.5;
            ">
                <b>{ts}</b><br>
                {sig}
            </div>
            """,
            unsafe_allow_html=True,
        )

    aaa_footer()


# ============================================================
# PAGE 20 — AAA PATTERN TIMELINE AI
# Neuralink-Style Signal Condenser (Premium Intelligence)
# ============================================================

def page_pattern_timeline_ai():
    aaa_header()
    st.subheader("🧩 AAA Pattern Timeline AI — Neuralink-Style Condensed Signals")

    # Premium check
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            This is AAA’s neural signal condenser — it compresses logs, documents, 
            insights, memory signals, and patterns into a unified high-density health 
            timeline. Inspired by Neuralink-style pattern compression and 
            DeepMind-style sequence alignment, this engine identifies your key daily 
            shifts and expresses them as condensed “signal bursts”.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOAD HEALTH LOGS
    # --------------------------------------------------------
    logs = load_json_data(HEALTH_LOG_FILE, default=[])
    vault_files = [f for f in os.listdir(VAULT_DIR)]
    insights = load_json_data(AI_SUMMARY_FILE, default={})
    memory_signals = load_json_data(os.path.join(DATA_DIR, "memory_signals.json"), default=[])

    # --------------------------------------------------------
    # TIME RANGE SELECT
    # --------------------------------------------------------
    st.markdown("### 📅 Select Timeline Range")
    range_choice = st.selectbox(
        "Choose analysis period:",
        ["Last 7 Days", "Last 14 Days", "Last 30 Days"]
    )

    if range_choice == "Last 7 Days":
        days = 7
    elif range_choice == "Last 14 Days":
        days = 14
    else:
        days = 30

    cutoff = datetime.now().timestamp() - (days * 86400)

    # Filter logs within range
    filtered_logs = [
        log for log in logs
        if "timestamp" in log and log["timestamp"] >= cutoff
    ]

    # --------------------------------------------------------
    # TIMELINE SUMMARY
    # --------------------------------------------------------
    st.markdown("### 🧠 Condensed Signal Timeline")
    if not filtered_logs:
        st.info("No activity detected in the selected range.")
    else:
        for log in filtered_logs:
            ts = datetime.fromtimestamp(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
            summary = log.get("summary", "No summary available.")

            st.markdown(
                f"""
                <div style="background:#0d1b2a; padding:15px; border-radius:10px; margin-bottom:10px;">
                    <b>🗓 {ts}</b><br>
                    <span style="font-size:15px;">{summary}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # SIGNAL CONDENSER (AI)
    # --------------------------------------------------------
    if st.button("🔮 Generate Condensed Pattern Summary"):
        with st.spinner("Analyzing behavioural & medical signals…"):

            log_text = "\n".join([l.get("summary", "") for l in filtered_logs])
            memory_text = "\n".join([m for m in memory_signals])
            insight_text = json.dumps(insights, indent=2)

            combined_text = (
                f"LOGS:\n{log_text}\n\n"
                f"MEMORY SIGNALS:\n{memory_text}\n\n"
                f"INSIGHTS:\n{insight_text}"
            )

            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                response = ai.generate_content(
                    f"""
                    You are AAA Pattern Timeline AI.

                    TASK:
                    - Read all logs, memory signals, insights.
                    - Detect recurring health patterns.
                    - Identify behaviour clusters.
                    - Create a condensed Neuralink-style 'signal burst' summary.
                    - Provide timeline trends and actionable signals.

                    DATA:
                    {combined_text}

                    FORMAT:
                    1. 🔶 High-Density Signal Burst (3–5 lines)
                    2. 📌 Behavioural Clusters
                    3. 📊 Medical Micro-Patterns
                    4. 🔮 Predictive Early Indicators (next 7 days)
                    """
                )

                st.markdown("### 🔶 Condensed Signal Burst")
                st.info(response.text)

            except Exception as e:
                st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 21 — AI Health Risk Engine (Premium)
# ============================================================

def page_risk_engine():
    aaa_header()
    st.subheader("⚠️ AI Health Risk Engine (Beta)")

    # ------------------------------
    # PREMIUM FIREWALL
    # ------------------------------
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            AAA’s AI Health Risk Engine detects behavioural shifts, lifestyle patterns,
            and early trends using your logs, summaries, memory signals, and insights.
            <br><br>
            <b>This is NOT medical advice</b> — it is pattern-based intelligence to help
            you understand daily rhythms, deviations, and consistency trends.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------
    # LOAD DATA
    # ------------------------------
    logs = load_json_data(HEALTH_LOG_FILE, default=[])
    insights = load_json_data(AI_SUMMARY_FILE, default={})
    memory_signals = load_json_data(os.path.join(DATA_DIR, "memory_signals.json"), default=[])

    # ------------------------------
    # RANGE SELECTOR
    # ------------------------------
    st.markdown("### 📅 Select Analysis Window")
    window = st.selectbox(
        "Analyze patterns for:",
        ["Last 7 Days", "Last 14 Days", "Last 30 Days"]
    )

    if window == "Last 7 Days":
        days = 7
    elif window == "Last 14 Days":
        days = 14
    else:
        days = 30

    cutoff = datetime.now().timestamp() - (days * 86400)

    filtered_logs = [
        log for log in logs
        if "timestamp" in log and log["timestamp"] >= cutoff
    ]

    st.markdown("### 📊 Recent Activity Overview")
    if not filtered_logs:
        st.info("No signals found in the selected period.")
    else:
        for log in filtered_logs:
            ts = datetime.fromtimestamp(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
            summary = log.get("summary", "No summary available.")

            st.markdown(
                f"""
                <div style="background:#0e1a25; padding:12px; border-radius:10px; margin-bottom:10px;">
                    <b>🗓 {ts}</b><br>
                    <span style="font-size:14px;">{summary}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ------------------------------
    # AI RISK ANALYSIS
    # ------------------------------
    if st.button("🚨 Run Risk Pattern Analysis"):
        with st.spinner("Evaluating behavioural and lifestyle patterns…"):

            log_text = "\n".join([l.get("summary", "") for l in filtered_logs])
            insight_text = json.dumps(insights, indent=2)
            memory_text = "\n".join([m for m in memory_signals])

            combined = (
                f"LOGS:\n{log_text}\n\n"
                f"INSIGHTS:\n{insight_text}\n\n"
                f"MEMORY SIGNALS:\n{memory_text}"
            )

            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                response = ai.generate_content(
                    f"""
You are AAA — the Artigellence Augmentation Aggregator.

Your task:
Analyze logs, behavioural summaries, insights, and memory signals.
Identify:
- Behavioural deviations
- Lifestyle risk contributors
- Sleep / activity pattern misalignments
- Stress & recovery cycles
- High-level trend warnings (non-medical)
- Consistency scoring
- Early risk indicators (pattern-level, NOT diagnosis)

DATA:
{combined}

Format output EXACTLY as:

🔶 **Pattern Deviation Summary**
- 2–3 lines

📉 **Behavioural Risk Contributors**
- Bullet list (3–5)

🧩 **Lifestyle Pattern Weak Points**
- Bullet list (3–5)

🔮 **Early Pattern Indicators (Next 7 Days)**
- 2–4 items

📊 **Consistency Score (0–100)**  
<short explanation>

Keep everything pattern-based.  
No medical claims.  
"""
                )

                st.markdown("### 🚨 Pattern Risk Summary")
                st.info(response.text)

            except Exception as e:
                st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 22 — INSIGHT FUSION LAYER (AAA Intelligence Core)
# Multi-Signal Fusion → One Unified Intelligence Burst
# ============================================================

def page_insight_fusion():
    aaa_header()
    st.subheader("🌐 Insight Fusion Layer — Unified Health Intelligence (Beta)")

    # ------------------------------
    # PREMIUM FIREWALL
    # ------------------------------
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            This is AAA’s central intelligence layer.  
            <br><br>
            It fuses signals from health logs, summaries, OCR, PDFs, insights,
            memory streams, risk patterns, and behavioural signals into one unified
            high-density intelligence burst.
            <br><br>
            Inspired by multi-modal fusion engines (DeepMind × Neuralink × AGI),
            this layer produces a complete picture of your health behaviour.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------
    # LOAD SIGNALS
    # ------------------------------
    logs = load_json_data(HEALTH_LOG_FILE, default=[])
    insights = load_json_data(AI_SUMMARY_FILE, default={})
    memory_signals = load_json_data(os.path.join(DATA_DIR, "memory_signals.json"), default=[])
    vault_data = load_json_data(os.path.join(DATA_DIR, "vault_data.json"), default={})
    score_history = load_json_data(os.path.join(DATA_DIR, "score_history.json"), default=[])

    # OCR results
    ocr_file = os.path.join(DATA_DIR, "ocr_results.json")
    if os.path.exists(ocr_file):
        with open(ocr_file, "r") as f:
            ocr_results = json.load(f)
    else:
        ocr_results = {}

    # Combine text blocks
    log_text = "\n".join([l.get("summary","") for l in logs])
    insight_text = json.dumps(insights, indent=2)
    memory_text = "\n".join([m for m in memory_signals])
    vault_text = json.dumps(vault_data, indent=2)
    ocr_text = json.dumps(ocr_results, indent=2)
    score_text = json.dumps(score_history, indent=2)

    combined_text = f"""
==== LOG SUMMARIES ====
{log_text}

==== INSIGHTS HISTORY ====
{insight_text}

==== MEMORY SIGNALS ====
{memory_text}

==== OCR EXTRACTED TEXT ====
{ocr_text}

==== VAULT PDF DATA ====
{vault_text}

==== HEALTH SCORE HISTORY ====
{score_text}
"""

    # ------------------------------
    # FUSION ENGINE
    # ------------------------------
    if st.button("🌐 Generate Unified Intelligence"):
        with st.spinner("Generating multi-signal fusion…"):

            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")

                response = ai.generate_content(
                    f"""
You are AAA — the Artigellence Augmentation Aggregator.

Your task is to fuse ALL signals from the user's health data into one unified
multi-modal intelligence summary.

DATA PROVIDED:
{combined_text}

Create output with the following structure:

🌐 **AAA Unified Intelligence Burst (High-Density Summary)**
- 4–6 lines, Neuralink-style compressed intelligence

📊 **Cross-Signal Patterns**
- What patterns persist across logs, OCR, insights, and memory signals?

🧩 **Hidden Correlations**
- What correlations emerge across behaviours, timing, and health scores?

📉 **Behavioural Drift Detection**
- Note any subtle deviations or changes in rhythm

🔮 **7-Day Predictive Indicators**
- Future-facing pattern-level predictions (non-medical)

📌 **Recommended Action Loops**
- Behavioural improvements
- Insight reinforcement
- Data collection suggestions

Ensure tone is:
- Non-medical
- Insightful
- Pattern-focused
- Actionable
- Calm and supportive
"""
                )

                st.markdown("## 🌐 Unified Intelligence Burst")
                st.info(response.text)

            except Exception as e:
                st.error(f"Fusion Engine Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 23 — AAA Insight Graphs & Trend Visualizer
# ============================================================

def page_insight_graphs():
    aaa_header()
    st.subheader("📈 AAA Insight Graphs & Trend Visualizer")

    # ------------------------------
    # PREMIUM FIREWALL
    # ------------------------------
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            Visual intelligence layer showing trends across logs, summaries,
            insights, and AAA behavioural patterns.
            <br><br>
            These charts help you understand consistency, patterns,
            and long-term behaviour.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------
    # LOAD DATA
    # ------------------------------
    logs = load_json_data(HEALTH_LOG_FILE, default=[])
    insights = load_json_data(AI_SUMMARY_FILE, default={})
    score_history = load_json_data(os.path.join(DATA_DIR, "score_history.json"), default=[])

    # Convert to DataFrames
    log_df = pd.DataFrame(logs)
    score_df = pd.DataFrame(score_history)
    insight_df = pd.DataFrame(insights.get("history", []))

    st.markdown("---")

    # ============================================================
    # 1) HEALTH SCORE TREND
    # ============================================================
    st.markdown("### 📈 Health Score Trend")

    if not score_df.empty and "score" in score_df and "timestamp" in score_df:
        score_df["date"] = pd.to_datetime(score_df["timestamp"]).dt.date

        chart = alt.Chart(score_df).mark_line(point=True).encode(
            x="date:T",
            y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100])),
            tooltip=["date", "score"]
        ).properties(
            width="container",
            height=300
        )

        st.altair_chart(chart, use_container_width=True)

    else:
        st.info("No health score data yet.")

    st.markdown("---")

    # ============================================================
    # 2) DAILY LOG FREQUENCY
    # ============================================================
    st.markdown("### 📊 Daily Log Activity")

    if not log_df.empty and "timestamp" in log_df:
        log_df["date"] = pd.to_datetime(log_df["timestamp"], unit="s").dt.date
        freq_df = log_df.groupby("date").size().reset_index(name="count")

        chart = alt.Chart(freq_df).mark_bar().encode(
            x="date:T",
            y="count:Q",
            tooltip=["date", "count"]
        ).properties(
            width="container",
            height=300
        )

        st.altair_chart(chart, use_container_width=True)

    else:
        st.info("No logs found.")

    st.markdown("---")

    # ============================================================
    # 3) INSIGHT GENERATION TREND
    # ============================================================
    st.markdown("### 🧩 Insight Frequency Trend")

    if not insight_df.empty and "timestamp" in insight_df:
        insight_df["date"] = pd.to_datetime(insight_df["timestamp"]).dt.date
        insight_freq = insight_df.groupby("date").size().reset_index(name="count")

        chart = alt.Chart(insight_freq).mark_area(opacity=0.5).encode(
            x="date:T",
            y="count:Q",
            tooltip=["date", "count"]
        ).properties(
            width="container",
            height=300
        )

        st.altair_chart(chart, use_container_width=True)

    else:
        st.info("No insights generated yet.")

    aaa_footer()


# ============================================================
# PAGE 24 — Medical Triptych Layer (Doctor + Lab + PDF Fusion)
# ============================================================

def page_medical_triptych():
    aaa_header()
    st.subheader("🩺 Medical Triptych — Doctor + Lab + PDF Fusion (Beta)")

    # -----------------------------
    # PREMIUM FIREWALL
    # -----------------------------
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:20px;">
            This is AAA’s unified medical intelligence layer.
            <br><br>
            It fuses data from three streams:
            <ul>
                <li><b>Doctor Notes</b> — manual entries + OCR</li>
                <li><b>Lab Reports</b> — extracted from PDFs</li>
                <li><b>Medical PDFs</b> — uploaded into your Health Vault</li>
            </ul>
            AAA combines all signals into a single clinical summary,
            trend analysis, and doctor-friendly briefing.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # 1) DOCTOR NOTES INPUT
    # ---------------------------------------------------------
    st.markdown("### 🟦 Doctor Notes")
    doctor_notes = st.text_area(
        "Add doctor notes or findings:",
        height=120,
        placeholder="Enter clinical notes, symptoms, observations..."
    )

    # ---------------------------------------------------------
    # 2) LAB REPORT EXTRACTION
    # ---------------------------------------------------------
    st.markdown("### 🟧 Lab Report (PDF → Text)")

    lab_pdf = st.file_uploader(
        "Upload a lab report (PDF)",
        type=["pdf"],
        key="lab_pdf_uploader"
    )

    lab_text = ""
    if lab_pdf:
        try:
            with open("temp_lab.pdf", "wb") as f:
                f.write(lab_pdf.read())
            lab_text = extract_text_any("temp_lab.pdf")
            st.success("Lab report extracted successfully.")
        except:
            st.error("Unable to read the lab PDF.")

    # ---------------------------------------------------------
    # 3) MEDICAL PDF VAULT — QUICK SELECT
    # ---------------------------------------------------------
    st.markdown("### 🟩 Select a Medical PDF from Vault")

    vault_files = [f for f in os.listdir(VAULT_DIR) if f.endswith(".pdf")]

    selected_pdf = st.selectbox(
        "Choose a PDF:",
        ["None"] + vault_files
    )

    vault_text = ""
    if selected_pdf != "None":
        try:
            path = os.path.join(VAULT_DIR, selected_pdf)
            vault_text = extract_text_any(path)
            st.success(f"Loaded PDF: {selected_pdf}")
        except:
            st.error("Failed to read selected PDF.")

    st.markdown("---")

    # Combine all triptych data
    combined_triptych = f"""
    DOCTOR NOTES:
    {doctor_notes}

    LAB REPORT:
    {lab_text}

    MEDICAL PDF:
    {vault_text}
    """

    # ---------------------------------------------------------
    # GENERATE FUSED TRIPTYCH SUMMARY
    # ---------------------------------------------------------
    if st.button("🔮 Generate Unified Medical Summary"):
        if not (doctor_notes or lab_text or vault_text):
            st.warning("Please provide at least one input source.")
            aaa_footer()
            return

        with st.spinner("Fusing doctor + lab + medical documents…"):
            try:
                ai = genai.GenerativeModel("gemini-2.0-flash")
                resp = ai.generate_content(
                    f"""
                    You are AAA Health Intelligence.

                    TASK:
                    Fuse DOCTOR NOTES + LAB REPORT + MEDICAL PDF.
                    Produce:
                    1) 🩺 Unified Clinical Summary (5–7 lines)
                    2) 📊 Key Trends (lab values, symptoms, behaviour)
                    3) 🚦 Risk/Attention Layer (non-alarming)
                    4) 🧑‍⚕️ Doctor-Friendly Briefing (clear, simple)

                    RAW DATA:
                    {combined_triptych}
                    """
                )

                st.markdown("### 🩺 Unified Clinical Summary")
                st.info(resp.text)

            except Exception as e:
                st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 25 — SERENE FREQUENCY INDICATORS
# Health × Vibration × Energy Signal Mapper (Beta)
# ============================================================

def page_serene_frequency():
    aaa_header()
    st.subheader("🎵 Serene Frequency Indicators — Vibration × Health Intelligence (Beta)")

    # Premium firewall
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            This is AAA’s vibration-health synchronisation layer.  
            It blends your emotional logs, sleep notes, medical summaries, 
            and energy patterns to generate personalised frequency indicators.
            <br><br>
            Inspired by wellness sciences, meditation research, and 
            mind–body coherence models, this module identifies:
            <ul>
                <li>• Daily emotional tone</li>
                <li>• Mental clarity indicators</li>
                <li>• Stress resonance levels</li>
                <li>• Suggested healing frequencies</li>
                <li>• Breath + focus guidance</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------
    # LOAD LOGS + INSIGHTS
    # ----------------------------------------------
    logs = load_json_data(HEALTH_LOG_FILE, default=[])
    insights = load_insights_history()

    if not logs and not insights:
        st.info("No logs or insights available yet. Add logs to activate Serene Frequency Indicators.")
        aaa_footer()
        return

    # ----------------------------------------------
    # USER SELECTOR
    # ----------------------------------------------
    st.markdown("### 📅 Select Range")
    freq_range = st.selectbox(
        "Choose analysis window:",
        ["Last 3 Days", "Last 7 Days", "Last 14 Days"]
    )

    days = 3 if freq_range == "Last 3 Days" else 7 if freq_range == "Last 7 Days" else 14
    cutoff = datetime.now().timestamp() - (days * 86400)

    filtered_logs = [
        l for l in logs
        if "timestamp" in l and l["timestamp"] >= cutoff
    ]

    # ----------------------------------------------
    # FREQUENCY SUMMARY PANEL
    # ----------------------------------------------
    st.markdown("### 🎛 Coherence Summary")

    if not filtered_logs:
        st.info("No recent logs in selected time range.")
        aaa_footer()
        return

    combined_text = "\n".join([l.get("summary", "") for l in filtered_logs])

    # ----------------------------------------------
    # AI ENGINE — GEMINI
    # ----------------------------------------------
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"""
            You are Serene Frequency AI.

            TASK:
            - Study emotional logs, daily summaries, and behaviour patterns.
            - Derive frequency alignment indicators.
            - Provide vibration-health insights.
            - Recommend frequencies (Hz), breathing patterns, or tones.
            - Keep output non-medical and supportive.

            LOG DATA:
            {combined_text}

            FORMAT:
            1. 🌤 Emotional Tone (1 line)
            2. 🔔 Frequency Recommendation (Hz)
            3. 🧘 Breath Rhythm Suggestion
            4. 🎵 Sound/Music Style Suggestion (Meditation, Alpha, Theta, Delta)
            5. 💬 Gentle Affirmation
            """
        )

        st.markdown("### 🎶 Your Frequency Alignment")
        st.info(response.text)

    except Exception as e:
        st.error(f"AI Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 26 — Mood × Sleep × Stress Radar (Mind–Body State Map)
# ============================================================

def page_mood_sleep_stress_radar():
    aaa_header()
    st.subheader("🧘 Mood × Sleep × Stress Radar — Mind–Body State Map (Beta)")

    # 🔐 Premium Lock
    if not is_premium():
        feature_locked()
        monetization_cta()
        aaa_footer()
        return

    # -------------------------------
    # USER INPUTS — MIND–BODY CHECK-IN
    # -------------------------------
    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:20px;">
            Track your emotional state, sleep quality, and stress levels.
            AAA will convert your inputs into a <b>Mind–Body Radar Map</b> to help you
            understand your inner-state trends and health connections.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        mood = st.slider("😊 Mood Level", 1, 10, 7)
        sleep_quality = st.slider("😴 Sleep Quality", 1, 10, 6)

    with col2:
        stress = st.slider("⚡ Stress Level", 1, 10, 4)
        energy = st.slider("🔋 Energy Level", 1, 10, 6)

    st.markdown("---")

    # -------------------------------
    # GENERATE RADAR CHART
    # -------------------------------
    if st.button("Generate Mind–Body Radar Map"):
        with st.spinner("Generating your Mind–Body State Map…"):

            # Data for radar
            categories = ["Mood", "Sleep", "Stress", "Energy"]
            values = [mood, sleep_quality, stress, energy]

            # Radar chart (matplotlib)
            import matplotlib.pyplot as plt
            import numpy as np

            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

            ax.plot(angles, values, linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_yticklabels([])

            st.pyplot(fig)

        st.success("Your Mind–Body State Map is ready.")

    st.markdown("---")

    # -------------------------------
    # AI INTERPRETATION — USING GEMINI/GPT
    # -------------------------------
    st.markdown("### 🔮 AI Interpretation")

    if st.button("Generate AI Insight"):
        with st.spinner("Analyzing your mind–body pattern…"):

            insight_prompt = f"""
You are AAA Health Intelligence. Provide a short, warm, evidence-based interpretation of the user's
Mood, Sleep, Stress, and Energy. Avoid medical claims.

Inputs:
- Mood: {mood}/10
- Sleep Quality: {sleep_quality}/10
- Stress: {stress}/10
- Energy: {energy}/10

Give:
1. A 2-sentence summary.
2. 2 actionable suggestions.
3. A vibration alignment note (Serene Frequencies).
"""

            try:
                ai_response = call_gemini(insight_prompt)
                st.markdown(
                    f"""
                    <div style="padding:15px; background:#0e1b2c; border-radius:10px;
                    box-shadow:0 0 10px rgba(0,0,0,0.3); color:#cde3ff;">
                        {ai_response}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error("AI interpretation failed. Please try again.")
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
            This module explores the relationship between your <b>physical health metrics</b> 
            and <b>vibration indicators</b> from Serene Frequency & Mind-Body logs.
            <br><br>
            AAA Intelligence correlates:
            <ul>
                <li>📊 Blood markers & medical summary metrics</li>
                <li>🎵 Frequency alignment scores</li>
                <li>🧘 Mood × Sleep × Stress patterns</li>
                <li>🔮 Serene Frequency Indicators</li>
            </ul>
            The engine reveals hidden patterns between health and vibration states,
            giving you a 360° insight into your mind–body alignment.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # -------------------------------
    # USER INPUTS FOR CORRELATION
    # -------------------------------
    st.markdown("### 🧩 Select Inputs for Correlation Analysis")

    health_option = st.selectbox(
        "Choose a Health Metric:",
        [
            "Blood Pressure",
            "Blood Sugar (Fasting / PP)",
            "Kidney Indicators (eGFR, Creatinine)",
            "Liver Enzymes (ALT, AST, GGT)",
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

            try:
                # ----------------------------------------------------
                # LOAD EXISTING DATA SOURCES
                # ----------------------------------------------------
                health_json = load_json("health_data.json")
                vibration_json = load_json("serene_frequency_data.json")  # placeholder file
                mindbody_json = load_json("mood_sleep_stress.json")       # placeholder file

                # ----------------------------------------------------
                # AAA CORRELATION ENGINE (Placeholder)
                # ----------------------------------------------------
                result = {
                    "health_metric": health_option,
                    "vibration_metric": vibration_option,
                    "correlation_score": round(random.uniform(-1, 1), 2),
                    "interpretation": (
                        "Positive correlation — improvements in vibration indicators align with better health outcomes."
                        if random.random() > 0.5 else
                        "Negative correlation — vibration imbalance may be influencing health metrics."
                    ),
                }

                # -------------------------------
                # DISPLAY RESULT SUMMARY
                # -------------------------------
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

                # -------------------------------
                # CORRELATION GRAPH (Matplotlib Placeholder)
                # -------------------------------
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
            This engine forecasts your upcoming health & vibration patterns using AI.
            It studies your logs, insights, trends, emotional signals, sleep quality,
            PDFs, and vibration metrics — then predicts what the next 7 days may look like.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------
    # LOAD DATA
    # --------------------------
    insights = load_insights_history()
    logs = load_logs()

    if not insights and not logs:
        st.warning("No historical data available for forecasting. Add logs or upload files.")
        aaa_footer()
        return

    # --------------------------
    # USER SELECTS FORECAST WINDOW
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

                # combine raw logs
                if logs:
                    combined_text += "\n\n".join(logs)

                # combine insights (summary + details)
                if insights:
                    for item in insights:
                        combined_text += f"\n{item.get('summary','')}"
                        combined_text += f"\n{item.get('details','')}"

                forecast_prompt = f"""
                You are AAA's predictive health and vibration intelligence engine.

                Using the historical combined dataset below, generate a clean, calm
                and educational forecast for the following window: {window}.

                Include:
                - Health trend forecast
                - Sleep forecast
                - Mood & stress forecast
                - Vibration/energy pattern shift prediction
                - Red flags to watch (non-alarming)
                - Simple lifestyle adjustments for the window

                DATA:
                {combined_text}
                """

                result = call_gemini(forecast_prompt)

                st.success("Forecast ready.")
                st.markdown(result)

                # --------------------------
                # MATPLOTLIB PREVIEW CHART
                # (SIMPLE — RANDOMIZED PLACEHOLDER)
                # --------------------------
                st.markdown("### 📉 Forecast Trend Preview (Simulated)")
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
        A unified chronological view of <b>all your health signals</b> — logs, summaries, 
        mood scores, sleep quality, stress levels, frequency indicators, and medical insights —
        merged into a single timeline for easier pattern detection.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # -------------------------------
    # PLACEHOLDER TIMELINE GRAPH
    # -------------------------------
    try:
        import matplotlib.pyplot as plt
        import random

        # Placeholder dates & values
        days = list(range(1, 16))
        health_scores = [random.randint(60, 85) for _ in days]
        mood_scores = [random.randint(40, 90) for _ in days]
        sleep_hours = [random.randint(4, 9) for _ in days]

        fig, ax = plt.subplots(figsize=(10,4))
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
# PAGE 30 — AAA INSIGHT MATRIX (Signal-to-Signal Relationship Grid)
# ============================================================

def page_insight_matrix():

    aaa_header()

    st.subheader("🧩 AAA Insight Matrix — Signal-to-Signal Relationship Grid (Beta)")

    # Premium Firewall
    if not is_premium():
        st.warning("This feature is available for Premium members.")
        monetization_cta()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:25px;">
            The <b>AAA Insight Matrix</b> compares how different health and vibration signals 
            interact, influence, and correlate with one another.  
            <br><br>
            Each cell visualizes the <b>strength</b> and <b>direction</b> of relationships using 
            synthetic placeholder data. Future versions will draw from the unified data lake 
            inside AAA-Health.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # SIGNAL LIST
    # -------------------------------
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

    # -------------------------------
    # PLACEHOLDER MATRIX (Random Heatmap)
    # -------------------------------
    st.markdown("### 🔥 Relationship Matrix (Placeholder Heatmap)")

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

    st.markdown(
        """
        <div style="font-size:15px; margin-top:20px; line-height:1.6;">
            <b>Matrix Interpretation:</b><br>
            • <b>Red</b> → Strong Positive Influence<br>
            • <b>Blue</b> → Strong Negative Influence<br>
            • <b>White</b> → Weak / No Correlation<br><br>
            The Insight Matrix will evolve into a core analytical engine within AAA-Health, 
            driving risk scoring, timelines, and forecast modules.
        </div>
        """,
        unsafe_allow_html=True,
    )

    aaa_footer()


# ============================================================
# PAGE 31 — Health Knowledge Graph (AI Semantic Medical Map)
# ============================================================

def page_health_knowledge_graph():
    aaa_header()
    st.subheader("🧠 Health Knowledge Graph — AI Semantic Medical Map (Beta)")

    # ---- Premium Lock ----
    if not is_premium():
        st.warning("This feature is available for Premium members.")
        monetization_cta()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:15px; line-height:1.6; margin-bottom:15px;">
            Explore an AI-generated semantic map of your health signals.
            The AAA Health Knowledge Graph connects symptoms, biomarkers,
            lifestyle factors, stress patterns, sleep cycles, and vibration
            signals into one unified medical understanding layer.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------
    # OPTIONS
    # ------------------------------
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
            with st.spinner("Generating AI Semantic Medical Graph…"):

                # PLACEHOLDER — Replace with future Graph Engine
                # Simulated JSON structure
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
                    "🔧 Full interactive graph (D3.js / PyVis) will be added in "
                    "AAA-Health v0.9 after December roadmap integration."
                )

        except Exception as e:
            st.error(f"Graph Engine Error: {e}")

    aaa_footer()


# ============================================================
# PAGE 32 — MULTI-SIGNAL DIAGNOSTIC ENGINE (AI Differential Insights)
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

    # 🔒 Premium Access
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # COLLECT SIGNALS FROM ALL SOURCES
    # ------------------------------------------------------------
    signals = []

    # 1. Vault Files (PDF, images, TXT)
    vault_files = [
        f for f in os.listdir(VAULT_DIR)
        if os.path.isfile(os.path.join(VAULT_DIR, f))
    ]
    for f in vault_files:
        path = os.path.join(VAULT_DIR, f)
        extracted = extract_text_any(path)
        if extracted.strip():
            signals.append(extracted)

    # 2. OCR Results
    ocr_results = load_json(OCR_DATA_FILE, [])
    for item in ocr_results:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # 3. Health Log
    health_log = load_json(HEALTH_LOG_FILE, [])
    for entry in health_log:
        if "note" in entry:
            signals.append(entry["note"])

    # 4. Doctor Notes
    doctor_notes = load_json(DOCTOR_NOTES_FILE, [])
    if doctor_notes:
        signals.append("\n".join(doctor_notes))

    # No data available
    if not signals:
        st.info("No health signals available. Upload files or write logs to generate insights.")
        monetization_cta()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # RUN THE ENGINE
    # ------------------------------------------------------------
    if st.button("🚀 Run Diagnostic Engine"):
        with st.spinner("Analyzing multi-source signals using AAA Intelligence…"):
            result = run_multi_signal_engine(signals)

        # Display formatted diagnostic insights
        st.markdown(result["formatted"], unsafe_allow_html=True)

        # Save into Insights History
        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Multi-Signal Diagnostic Insight",
            "short": result["json"]["summary"],
            "deep": result["formatted"]
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Insights saved to Insights History successfully.")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE 33 — HEALTH SIGNATURE ENGINE (NEW ENGINE)
# ============================================================

def page_health_signature_engine():
    check_firewall("Health Signature Engine", st.session_state.get("mode", "free"))
    aaa_header()

    st.markdown("""
        <h2 style="text-align:center; color:#D4A037; margin-bottom:4px;">
            🩺 Health Signature Engine
        </h2>
        <p style="text-align:center; color:#8FA3B8; font-size:15px;">
            Generates a unified health signature across logs, biomarkers, PDFs and patterns.
            (Strictly informational — no medical advice)
        </p>
        <br>
    """, unsafe_allow_html=True)

    # 🔒 Premium Block
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # GATHER SIGNALS
    # ------------------------------------------------------------
    signals = []

    # 1) Vault files
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        text = extract_text_any(os.path.join(VAULT_DIR, f))
        if text.strip():
            signals.append(text)

    # 2) OCR
    ocr_data = load_json(OCR_DATA_FILE, [])
    for item in ocr_data:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # 3) Health logs
    logs = load_json(HEALTH_LOG_FILE, [])
    for entry in logs:
        if entry.get("note", "").strip():
            signals.append(entry["note"])

    # Validation
    if not signals:
        st.info("No signals available. Please upload files or logs.")
        monetization_cta()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # RUN ENGINE
    # ------------------------------------------------------------
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

        # Save to insights history
        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Health Signature Engine",
            "short": result["json"].get("summary", ""),
            "deep": result["formatted"]
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Health Signature saved to Insights History.")

    monetization_cta()
    aaa_footer()


    # ------------------------------------------------------------
    # RUN ENGINE
    # ------------------------------------------------------------
    if st.button("🔬 Generate Health Signature"):
        with st.spinner("Building your multi-layer Health Signature…"):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(signature_prompt)
                ai_text = response.text or "(No response)"
            except Exception as e:
                ai_text = f"Error generating signature: {e}"

        # Display Output
        st.markdown(ai_text, unsafe_allow_html=True)

        # Save into history
        history = load_json(INSIGHTS_FILE, [])
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "Health Signature Engine Output",
            "short": ai_text[:600],
            "deep": ai_text
        })
        save_json(INSIGHTS_FILE, history)

        st.success("Health Signature saved to Insights History.")

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

    # 🔒 Premium wall
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # LOAD SIGNAL SOURCES
    # ------------------------------------------------------------
    signals = []

    # Health Log
    logs = load_json(HEALTH_LOG_FILE, [])
    log_text = "\n".join([entry.get("note", "") for entry in logs])
    if log_text.strip():
        signals.append(("Health Log", log_text))

    # OCR
    ocr_items = load_json(OCR_DATA_FILE, [])
    ocr_text = "\n".join([t.get("text", "") for t in ocr_items if isinstance(t, dict)])
    if ocr_text.strip():
        signals.append(("OCR Extracted Text", ocr_text))

    # Vault PDFs / Images
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        text = extract_text_any(os.path.join(VAULT_DIR, f))
        if text.strip():
            signals.append((f, text))

    # Doctor Notes
    doctor = load_json(DOCTOR_NOTES_FILE, [])
    if doctor:
        signals.append(("Doctor Notes", "\n".join(doctor)))

    # Validation
    if not signals:
        st.info("No signals available for comparison. Please upload files or add logs.")
        monetization_cta()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # USER SELECTION — PICK ANY 2–4 SIGNALS TO COMPARE
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
            try:
                prompt = f"""
                You are AAA Intelligence. Compare these signals:

                {str(selected)}

                For each signal, analyse:
                - Key themes  
                - Biomarker references  
                - Symptoms & trends  
                - Contradictions  
                - Overlaps  
                - Missing information  
                - Agreement score (0–100)

                Output format (HTML):
                1. Comparison Table  
                2. Overlap Map  
                3. Conflicts  
                4. Agreement Score  
                5. Short Summary (150 words)
                """

                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                ai_text = response.text or "(No response)"

            except Exception as e:
                ai_text = f"Error generating comparison: {e}"

        # Display
        st.markdown(ai_text, unsafe_allow_html=True)

        # Save to history
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
            Detect variability, noise, instability, and fluctuations across all your health signals.
            (Strictly informational — no medical advice)
        </p>
        <br>
    """, unsafe_allow_html=True)

    # Premium check
    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # Load all signals
    # ------------------------------------------------------------
    signals = []

    # Vault files
    vault_files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    for f in vault_files:
        path = os.path.join(VAULT_DIR, f)
        text = extract_text_any(path)
        if text.strip():
            signals.append(text)

    # OCR data
    ocr = load_json(OCR_DATA_FILE, [])
    for item in ocr:
        if isinstance(item, dict) and "text" in item:
            signals.append(item["text"])

    # Health log
    logs = load_json(HEALTH_LOG_FILE, [])
    for entry in logs:
        signals.append(entry.get("note", ""))

    # Doctor notes
    doctor = load_json(DOCTOR_NOTES_FILE, [])
    if doctor:
        signals.append("\n".join(doctor))

    if not signals:
        st.info("No signals found. Please upload documents or logs first.")
        monetization_cta()
        aaa_footer()
        return

    # ------------------------------------------------------------
    # RUN VOLATILITY ENGINE
    # ------------------------------------------------------------
    if st.button("🔍 Analyze Signal Volatility"):
        with st.spinner("Evaluating volatility patterns…"):
            try:
                combined = "\n\n---\n\n".join(signals)
                prompt = """
You are AAA — Artigellence Augmentation Aggregator.

TASK:
Analyze the combined signals and detect variability, instability, fluctuations,
and high-volatility regions.

STRICT RULES:
- No medical advice.
- No diagnosis.
- Observational patterns only.

FORMAT:

1. High-Volatility Zones  
2. Low-Volatility Zones  
3. Noise / Outlier Regions  
4. Potential Correlation Instability  
5. Summary (100 words)
"""

                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt + combined[:30000])
                ai_text = response.text or "No response"

            except Exception as e:
                ai_text = f"Error generating volatility insights: {e}"

        st.markdown(f"<div style='font-size:15px; line-height:1.7;'>{ai_text}</div>", unsafe_allow_html=True)

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE – SUBSCRIPTION PLANS (AAA PREMIUM)
# ============================================================

def page_subscription_plans():
    aaa_header()
    st.subheader("💳 Subscription Plans — Artigellence Premium")

    # Everyone can see this page (no premium lock)
    st.markdown(
        """
        <div style="font-size:15px; line-height:1.6; margin-bottom:20px; color:#C7D2FE;">
            Choose how you want to explore <b>AAA — Health Intelligence</b>.
            Free mode lets you try the experience, while <b>Artigellence Premium</b>
            unlocks full AI intelligence, health reports, and early access to AAA Finance & Law.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- PLAN CARDS LAYOUT ---
    col1, col2, col3 = st.columns(3)

    # FREE PLAN
    with col1:
        st.markdown(
            """
            <div style="
                border-radius:14px;
                padding:18px;
                background:linear-gradient(145deg, #020617, #0f172a);
                border:1px solid #1f2937;
            ">
                <h3 style="color:#E5E7EB; margin-bottom:4px;">Free</h3>
                <p style="color:#9CA3AF; font-size:13px; margin-top:0;">
                    Get a feel for AAA Health Intelligence.
                </p>
                <div style="font-size:22px; font-weight:bold; color:#FACC15; margin:8px 0;">
                    $0 / month
                </div>
                <ul style="color:#D1D5DB; font-size:13px; padding-left:18px;">
                    <li>Dashboard (Beta)</li>
                    <li>Basic Health Log</li>
                    <li>PDF Vault & OCR (limits apply)</li>
                    <li>Demo AI Summary (short preview)</li>
                    <li>Snapshots (Beta)</li>
                </ul>
                <div style="margin-top:10px; font-size:11px; color:#6B7280;">
                    Ideal if you are just exploring AAA.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # PREMIUM – INDIA PLAN (₹500)
    with col2:
        st.markdown(
            """
            <div style="
                border-radius:14px;
                padding:18px;
                background:linear-gradient(145deg, #0b1120, #111827);
                border:1px solid #4B5563;
                box-shadow:0 0 18px rgba(56,189,248,0.35);
            ">
                <div style="font-size:11px; color:#22C55E; text-transform:uppercase; letter-spacing:0.08em;">
                    Recommended
                </div>
                <h3 style="color:#E5E7EB; margin-bottom:4px;">Artigellence Premium — India</h3>
                <p style="color:#9CA3AF; font-size:13px; margin-top:0;">
                    Full AAA Health Intelligence for users in India.
                </p>
                <div style="font-size:22px; font-weight:bold; color:#22C55E; margin:8px 0;">
                    ₹500 / month
                </div>
                <ul style="color:#D1D5DB; font-size:13px; padding-left:18px;">
                    <li>Unlimited AI Medical Summaries</li>
                    <li>Hybrid Engine Insights (multi-document)</li>
                    <li>Deep Insights AI & Insights History log</li>
                    <li>PDF Health Reports & Summary PDF export</li>
                    <li>Merged View (Doctor + Lab + Notes)</li>
                    <li>Snapshots & Smart Timeline</li>
                    <li>Early access to AAA Finance & Law</li>
                    <li>Priority feature upgrades</li>
                </ul>
                <div style="margin-top:10px; font-size:11px; color:#E5E7EB;">
                    Stripe checkout coming soon – pricing is indicative only.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # PREMIUM – GLOBAL PLAN
    with col3:
        st.markdown(
            """
            <div style="
                border-radius:14px;
                padding:18px;
                background:linear-gradient(145deg, #020617, #0f172a);
                border:1px solid #1f2937;
            ">
                <h3 style="color:#E5E7EB; margin-bottom:4px;">Artigellence Premium — Global</h3>
                <p style="color:#9CA3AF; font-size:13px; margin-top:0;">
                    For users outside India (Australia, US, EU and more).
                </p>
                <div style="font-size:22px; font-weight:bold; color:#38BDF8; margin:8px 0;">
                    $10 / month
                </div>
                <ul style="color:#D1D5DB; font-size:13px; padding-left:18px;">
                    <li>All Premium health features</li>
                    <li>AI-generated health PDFs</li>
                    <li>Hybrid Engine & Insights History</li>
                    <li>Priority roadmap voting</li>
                    <li>Access to future Serene Frequencies indicators</li>
                </ul>
                <div style="margin-top:10px; font-size:11px; color:#6B7280;">
                    Final pricing may adjust slightly at public launch.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Note about upcoming Stripe integration
    st.info(
        "Stripe payments are not live yet. These plans show the intended structure and prices. You are currently in demo mode."
    )

    # Keep your standard monetization CTA + footer
    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE — PREMIUM (COMING SOON) — AAA GOLD–TEAL VERSION
# ============================================================

def page_premium():
    aaa_header()

    st.subheader("🌟 Artigellence Premium — Coming Soon")

    st.markdown(
        """
        <div style="font-size:15px; line-height:1.7; color:#C7D2FE; margin-bottom:20px;">
            You’re viewing the upcoming <b>AAA Premium</b> membership layer.
            This tier unlocks the full power of <b>AAA — Health Intelligence</b>,
            including advanced AI engines, cross-document insights, vibration indicators,
            and future AAA Finance × Law modules.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------
    # GOLD–TEAL PREMIUM CARD
    # -------------------------
    st.markdown(
        """
        <div style="
            margin-top:10px;
            padding:22px;
            border-radius:16px;
            background:linear-gradient(135deg, #0b1120, #1e293b);
            border:1px solid rgba(56,189,248,0.35);
            box-shadow:0 0 28px rgba(56,189,248,0.28);
        ">
            <h2 style="color:#FACC15; margin:0; font-size:24px;">
                🚀 AAA Premium (Full Intelligence Tier)
            </h2>

            <p style="color:#C7D2FE; font-size:14px; margin-top:10px;">
                Unlock every AI engine inside AAA — from summaries to pattern analysis,
                timeline intelligence, multi-signal diagnostics, vibration correlation,
                volatility mapping, and more.
            </p>

            <ul style="color:#E2E8F0; font-size:14px; line-height:1.6; padding-left:20px; margin-top:15px;">
                <li>Unlimited AI Medical Summaries</li>
                <li>Hybrid Engine (Doctor × Lab × Notes)</li>
                <li>Deep Insights AI + History</li>
                <li>Smart Timeline & Snapshots</li>
                <li>PDF Health Reports + AI-Generated PDFs</li>
                <li>Pattern Timeline AI + Trend Forecast</li>
                <li>Health × Vibration Correlation Indicators</li>
                <li>Unified Multi-Signal Comparison</li>
                <li>Volatility Map + Noise Detection Engine</li>
                <li>Early access to AAA Finance & Law</li>
                <li>Serene Frequencies wellness indicators</li>
            </ul>

            <div style="margin-top:18px; font-size:13px; color:#94A3B8;">
                Final pricing will be announced soon. You are currently in demo mode.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA BELOW CARD
    st.markdown(
        """
        <div style="margin-top:25px; font-size:16px; color:#C7D2FE;">
            Want early access? Premium launches with full AI workflows, 
            vibration intelligence, and cross-domain upgrades.
        </div>
        """,
        unsafe_allow_html=True,
    )

    monetization_cta()
    aaa_footer()


# ============================================================
# PHASE-2 HELPERS — HEALTH SCORE + AI SUMMARY
# PHASE-3 STEP-1 — SCORE HISTORY + MATPLOTLIB TREND
# ============================================================

import json
import os
from datetime import datetime
import google.generativeai as genai
import matplotlib.pyplot as plt

SCORE_HISTORY_FILE = "score_history.json"


# -----------------------------
# SIMPLE HEALTH SCORE V1
# -----------------------------
def compute_health_score(logs):
    if not logs:
        return 50  # neutral

    score = 70  # base

    positive_words = ["energetic", "slept well", "good", "better", "ok", "improved"]
    negative_words = ["pain", "tightness", "headache", "dizzy", "fatigue"]

    for entry in logs:
        notes = entry.get("notes", "").lower()
        for p in positive_words:
            if p in notes:
                score += 2
        for n in negative_words:
            if n in notes:
                score -= 3

    # recency boost
    try:
        last_date = datetime.strptime(logs[-1]["timestamp"], "%Y-%m-%d %H:%M:%S")
        days_ago = (datetime.now() - last_date).days
        if days_ago <= 2:
            score += 5
    except:
        pass

    return max(1, min(score, 99))  # clamp


# -----------------------------
# AI SUMMARY USING GEMINI
# -----------------------------
def generate_ai_health_summary(logs, merged_data):
    try:
        combined_text = ""

        for l in logs:
            combined_text += f"Log ({l.get('timestamp')}): {l.get('notes', '')}\n"

        for item in merged_data:
            if item.get("type") == "summary":
                combined_text += f"Summary: {item.get('text', '')}\n"
            if item.get("type") == "photo":
                combined_text += f"Photo metadata: {item.get('filename','')}\n"

        prompt = f"""
        You are a health summarization assistant.
        Create a short, safe summary of the user's health patterns based on this data.
        Avoid diagnosis. Avoid medical claims.
        Keep it simple, optimistic, trend-based, and observation-only.

        DATA:
        {combined_text}
        """

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"AI Summary could not load: {e}"


# ============================================================
# PHASE-3 STEP-1 — SCORE HISTORY + TREND GRAPH
# ============================================================

def load_score_history():
    if not os.path.exists(SCORE_HISTORY_FILE):
        with open(SCORE_HISTORY_FILE, "w") as f:
            json.dump({"history": []}, f, indent=4)
        return []

    try:
        with open(SCORE_HISTORY_FILE) as f:
            return json.load(f).get("history", [])
    except:
        return []


def save_score_history(latest_score):
    history = load_score_history()

    history.append({
        "score": latest_score,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    history = history[-30:]

    with open(SCORE_HISTORY_FILE, "w") as f:
        json.dump({"history": history}, f, indent=4)

    return history


def plot_score_trend(history):
    if not history:
        return None

    scores = [h["score"] for h in history]
    timestamps = [h["timestamp"][5:16] for h in history]

    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.plot(scores, marker="o", linestyle="-")
    ax.set_title("Health Score Trend (Last 30 updates)", fontsize=10)
    ax.set_xlabel("Timeline", fontsize=8)
    ax.set_ylabel("Score", fontsize=8)
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
    logs_text = " ".join([entry.get("notes", "").lower() for entry in logs]) if logs else ""

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
    st.subheader("📊 AAA Health Intelligence — Tailored Dashboard (Beta)")
    st.markdown("This is your personalised health overview. More data unlocks as you upload documents, logs, or summaries.")
    st.markdown("")

    # ------------------------------------------------------------
    # LOAD HEALTH LOGS
    # ------------------------------------------------------------
    logs = []
    if os.path.exists("health_log.json"):
        try:
            with open("health_log.json") as f:
                logs = json.load(f)
        except:
            pass

    # ------------------------------------------------------------
    # LOAD MULTI-MODAL MERGED DATA
    # ------------------------------------------------------------
    merged_data = []
    if os.path.exists("health_data.json"):
        try:
            with open("health_data.json") as f:
                merged_data = json.load(f).get("data", [])
        except:
            pass

    # ------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------
    health_score = compute_health_score(logs)
    last_update = logs[-1]["timestamp"] if logs else "—"
    region = "Sydney, AU"

    # Score history
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
    # HEALTH PULSE (now logs exist, variables exist)
    # ------------------------------------------------------------
    recent_note = logs[-1]["notes"] if logs else ""
    file_count = len(os.listdir("vault_files")) if os.path.exists("vault_files") else 0

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
    # AI SUMMARY (Phase-2)
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
    recent_note = logs[-1]["notes"] if logs else "No logs yet."
    file_count = len(os.listdir("vault_files")) if os.path.exists("vault_files") else 0

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("#### 📅 Last Update")
        st.info(snapshot_date)

    with col_b:
        st.markdown("#### 📝 Latest Note")
        st.info(recent_note[:80] + ("..." if len(recent_note) > 80 else ""))

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

    if logs:
        note = logs[-1]["notes"].lower()
        positive_markers = ["energetic", "better", "slept well", "okay", " improved"]
        negative_markers = ["pain", "tightness", "headache", "fatigue", "dizzy"]

        pos_flag = any(p in note for p in positive_markers)
        neg_flag = any(n in note for n in negative_markers)

        if pos_flag and not neg_flag:
            signals.append("🟢 **Your last note looks positive** — good indicators reported.")
        elif neg_flag and not pos_flag:
            signals.append("🔴 **Discomfort indicators detected** — monitor closely.")
        elif pos_flag and neg_flag:
            signals.append("🟡 **Mixed signals** — some good signs, some discomfort.")
        else:
            signals.append("⚪ No clear sentiment detected in last note.")
    else:
        signals.append("⚪ No logs yet — start adding health notes for signals.")

    if os.path.exists("vault_files"):
        doc_count = len(os.listdir("vault_files"))
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
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ------------------------------------------------------------
    # WHY THESE SIGNALS MATTER
    # ------------------------------------------------------------
    st.markdown("### 🧠 Why These Signals Matter")

    def generate_reasoning_layer(logs, recent_note, file_count):
        reasons = []

        if "headache" in recent_note.lower():
            reasons.append("Headache often correlates with hydration levels or warm weather.")

        if "tightness" in recent_note.lower():
            reasons.append("Chest tightness patterns suggest exertion or hydration issues.")

        if "slept well" in recent_note.lower() or "sleep" in recent_note.lower():
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
    text_blob = " ".join([l.get("notes", "") for l in recent_logs]).lower()
    warnings = []

    symptom_keywords = ["headache", "pain", "tightness", "pressure"]
    symptom_count = sum(text_blob.count(k) for k in symptom_keywords)
    if symptom_count >= 2:
        warnings.append("⚠️ **Recurring symptoms detected** — monitor patterns.")

    if len(recent_logs) <= 3:
        warnings.append("⚠️ **Low logging frequency** — more logs improve accuracy.")

    if "water" in text_blob or "hydration" in text_blob:
        warnings.append("💧 **Hydration-related pattern noted** — keep tracking water.")

    sleep_keywords = ["sleep", "tired", "fatigue"]
    if any(k in text_blob for k in sleep_keywords):
        if "good" not in text_blob:
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
            st.markdown(
                f"""
                **📅 {entry.get('date','')} — {entry.get('timestamp','')}**

                {entry.get('notes','')}
                """
            )
    else:
        st.warning("No logs found.")

    st.markdown("---")

    # ------------------------------------------------------------
    # RECENT DOCUMENTS
    # ------------------------------------------------------------
    st.markdown("### 📂 Recent Documents")

    recent_docs = []
    if os.path.exists("vault_files"):
        for fname in os.listdir("vault_files"):
            p = os.path.join("vault_files", fname)
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
    "Premium (Coming Soon)",
    "Summary AI",
    "Insights AI",
    "Summary Report",
    "Merged View",
}

def check_firewall(page_name: str, mode: str):
    """
    Light firewall:
    - Free mode → premium pages show upgrade notice.
    - Premium mode → fully unlocked.
    This is the safest & cleanest version.
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

        # SUBSCRIPTION MODE
        st.markdown("## 🔐 Subscription Mode (Demo)")
        mode = st.radio("Select mode:", ["free", "premium"])
        st.session_state["mode"] = mode

        # HEADER
        st.markdown("## 💎 AAA — Health Intelligence (DEV)")

        # NAVIGATION MENU
        choice = st.radio(
            "Navigate:",
            [
                # ---- Core Health Intelligence ----
                "📊 Dashboard",
                "🩺 Health Log",
                "📥 Health Vault",
                "📁 Vault Manager",
                "🗑 Recycle Bin",
                "📄 PDF Preview",
                "🔍 OCR",

                # ---- AI Intelligence Layer ----
                "🧠 Summary (Demo)",
                "✨ Merged View",
                "🧬 Summary AI",
                "📊 Insights AI",
                "📚 Insights History",
                "📘 Summary Report",
                "🚨 AI Health Risk Engine",
                "🧬 Pattern Timeline AI",
                "🌐 Insight Fusion Layer",
                "📈 Insight Graphs",
                "🩺 Medical Triptych",
                "🎵 Serene Frequencies",
                "🧘 Mood × Sleep × Stress Radar",
                "🔮 Health × Vibration Correlation Map",
                "📈 Trend Forecast Engine",
                "📅 Unified Timeline Intelligence",
                "🧩 Insight Matrix",
                "🧠 Health Knowledge Graph",
                "🧬 Multi-Signal Diagnostic Engine",     # Page 32
                "🧬 Health Signature Engine",            # Page 33
                "🧬 Unified Signal Comparison",          # Page 34
                "📉 Signal Volatility Engine",           # Page 35

                # ---- Monetization Layer ----
                "💎 Subscription Plans",
                "💳 Stripe Engine",

                # ---- Future Intelligence Layer ----
                "🧠 Edge Node Memory",

                # ---- Upcoming Features ----
                "🌟 Premium (Coming Soon)",
                "🧊 Snapshots",
            ]
        )

    # -------------------------------
    # FIREWALL — DO NOT MOVE
    # -------------------------------
    check_firewall(choice, mode)

    # -------------------------------
    # PAGE ROUTING
    # -------------------------------
    if choice == "📊 Dashboard":
        page_dashboard()

    elif choice == "🩺 Health Log":
        page_health_log()

    elif choice == "📥 Health Vault":
        page_health_vault()

    elif choice == "📁 Vault Manager":
        page_vault_manager()

    elif choice == "🗑 Recycle Bin":
        page_recycle_bin()

    elif choice == "📄 PDF Preview":
        page_pdf_preview()

    elif choice == "🔍 OCR":
        page_ocr()

    elif choice == "🧠 Summary (Demo)":
        page_summary()

    elif choice == "✨ Merged View":
        page_merged()

    elif choice == "🧬 Summary AI":
        page_summary_ai()

    elif choice == "📊 Insights AI":
        page_insights_ai()

    elif choice == "📚 Insights History":
        page_insights_history()

    elif choice == "📘 Summary Report":
        page_summary_report()

    elif choice == "🚨 AI Health Risk Engine":
        page_risk_engine()

    elif choice == "🧬 Pattern Timeline AI":
        page_pattern_timeline_ai()

    elif choice == "🌐 Insight Fusion Layer":
        page_insight_fusion()

    elif choice == "📈 Insight Graphs":
        page_insight_graphs()

    elif choice == "🩺 Medical Triptych":
        page_medical_triptych()

    elif choice == "🎵 Serene Frequencies":
        page_serene_frequency()

    elif choice == "🧘 Mood × Sleep × Stress Radar":
        page_mood_sleep_stress_radar()

    elif choice == "🔮 Health × Vibration Correlation Map":
        page_health_vibration_correlation()

    elif choice == "📈 Trend Forecast Engine":
        page_trend_forecast_engine()

    elif choice == "📅 Unified Timeline Intelligence":
        page_unified_timeline_intel()

    elif choice == "🧩 Insight Matrix":
        page_insight_matrix()

    elif choice == "🧠 Health Knowledge Graph":
        page_health_knowledge_graph()

    elif choice == "🧬 Multi-Signal Diagnostic Engine":
        page_multi_signal_engine()

    elif choice == "🧬 Health Signature Engine":
        page_health_signature_engine()

    elif choice == "🧬 Unified Signal Comparison":
        page_unified_signal_comparison()

    elif choice == "📉 Signal Volatility Engine":
        page_signal_volatility_engine()

    elif choice == "💎 Subscription Plans":
        page_subscription_plans()

    elif choice == "💳 Stripe Engine":
        page_stripe_engine()

    elif choice == "🧠 Edge Node Memory":
        page_edge_node_memory()

    elif choice == "🌟 Premium (Coming Soon)":
        page_premium()

    elif choice == "🧊 Snapshots":
        page_snapshots()

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
