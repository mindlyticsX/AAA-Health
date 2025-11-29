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
import stripe          # Stripe for future checkout integration

# ============================================================
# PATHS & DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "aaa_health_data")
VAULT_DIR = os.path.join(DATA_DIR, "vault_files")
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")
RECYCLE_BIN_DIR = os.path.join(DATA_DIR, "recycle_bin")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(RECYCLE_BIN_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

HEALTH_LOG_FILE = os.path.join(DATA_DIR, "health_log.json")
OCR_DATA_FILE = os.path.join(DATA_DIR, "ocr_results.json")
PHOTO_DATA_FILE = os.path.join(DATA_DIR, "photo_data.json")
MERGED_DATA_FILE = os.path.join(DATA_DIR, "merge_health_data.py")
AI_SUMMARY_FILE = os.path.join(DATA_DIR, "ai_summary.json")
SUMMARY_REPORT_PDF = os.path.join(DATA_DIR, "health_summary_report.pdf")

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
# PAGE — SUBSCRIPTION PLANS (AAA PREMIUM)
# ============================================================

def page_subscription_plans():
    aaa_header()
    st.subheader("💎 AAA Premium — Unlock Full Health Intelligence")

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:20px;">
            Upgrade to AAA Premium to access advanced AI-powered health insights,
            deep report intelligence, professional summaries, and upcoming Finance
            and Law intelligence modules. Designed to give you clarity, control,
            and confidence.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # FREE vs PREMIUM COMPARISON
    # -------------------------------
    st.markdown(
        """
        <style>
            .plan-card {
                background-color: #0B1523;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #1f2b3a;
                margin-bottom: 20px;
            }
            .gold-title {
                color: #D4A037;
                font-size: 20px;
                font-weight: 600;
            }
            .teal {
                color: #00A6C8;
            }
            .gold {
                color: #F2C678;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # FREE PLAN
    st.markdown(
        """
        <div class="plan-card">
            <div class="gold-title">🆓 Free Plan</div>
            <ul>
                <li>Health Log (basic)</li>
                <li>Upload PDF & Images</li>
                <li>Basic OCR</li>
                <li>Demo Summary (sample only)</li>
                <li>Access to Dashboard</li>
                <li>Snapshots</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # PREMIUM PLAN
    st.markdown(
        """
        <div class="plan-card">
            <div class="gold-title">💎 AAA Premium</div>
            <ul>
                <li class="teal">Advanced AI Summaries</li>
                <li class="teal">Insights AI (Deep Medical Intelligence)</li>
                <li class="teal">Insights History Viewer</li>
                <li class="teal">Merged View (Multi-Document Intelligence)</li>
                <li class="teal">PDF Summary Reports (Exportable)</li>
                <li class="teal">Priority Model Processing</li>
                <li class="gold">Coming December 2025: Rich Analytics Dashboard</li>
                <li class="gold">Coming Jan–Feb 2026: Finance Intelligence</li>
                <li class="gold">Coming Feb 2026: Law Intelligence</li>
                <li class="gold">AI Nodes: Personal AI Agents</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # PRICING BOX
    # -------------------------------
    st.markdown(
        """
        <div style="
            background-color:#0B1523;
            border: 1px solid #2c3e50;
            border-radius: 12px;
            padding: 20px;
            margin-top: 10px;
        ">
            <h3 style="color:#D4A037;">💎 Early Access Pricing</h3>
            <p style="line-height:1.6;">
                <span style="font-size:28px; color:#00A6C8;"><b>$10 / month</b></span><br>
                <span style="color:#F2C678;">(Early access — pricing may change after launch)</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA BUTTON
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Upgrade to AAA Premium 💎"):
        st.info("Subscription system coming soon — launching December 2025!")

    monetization_cta()
    aaa_footer()


# ============================================================
# PAGE — PREMIUM (COMING SOON) — AAA GOLD–TEAL VERSION
# ============================================================

def page_premium():
    aaa_header()
    
    st.markdown(
        """
        <div style='text-align:center; margin-bottom:20px;'>
            <img src='https://raw.githubusercontent.com/mindlyticsx/AAA-Health/main/assets/aaa_logo.png'
                 width='140'>
        </div>
        <h2 style='text-align:center; color:#D4A037;'>🌟 Premium Features — Coming Soon</h2>
        <p style='text-align:center; max-width:720px; margin:auto; line-height:1.6;'>
            We’re building advanced <span style='color:#00A6C8;'>AAA Intelligence</span> features 
            to help you take control of your Health, Finance, and Law data like never before.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # PREMIUM FEATURE BLOCK
    # -------------------------------
    st.markdown(
        """
        <div style="
            background-color:#0B1523;
            border:1px solid #1f2b3a;
            border-radius:12px;
            padding:20px;
            margin-top:25px;
        ">
            <h3 style="color:#D4A037;">💎 What Premium Will Unlock</h3>
            <ul style="line-height:1.8;">
                <li><span style='color:#00A6C8;'>Deep Health Intelligence Reports</span></li>
                <li><span style='color:#00A6C8;'>Trends, Risks & Early Warnings</span></li>
                <li><span style='color:#00A6C8;'>Multi-file Comparisons (Merged View)</span></li>
                <li><span style='color:#00A6C8;'>Insights AI — Medical Reasoning</span></li>
                <li><span style='color:#00A6C8;'>Insights History Viewer</span></li>
                <li><span style='color:#00A6C8;'>Unlimited PDF & CSV Exports</span></li>
                <li><span style='color:#00A6C8;'>AI-assisted Recommendations</span></li>
                <li><span style='color:#00A6C8;'>Priority Model Processing</span></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # ROADMAP BLOCK
    # -------------------------------
    st.markdown(
        """
        <div style="
            background-color:#0B1523;
            border:1px solid #2c3e50;
            border-radius:12px;
            padding:20px;
            margin-top:25px;
        ">
            <h3 style="color:#D4A037;">🗓 Roadmap</h3>
            <ul style="line-height:1.8;">
                <li><span style='color:#F2C678;'>December 2025:</span> Rich Analytics Dashboard</li>
                <li><span style='color:#F2C678;'>January 2026:</span> AAA Finance Intelligence (Beta)</li>
                <li><span style='color:#F2C678;'>February 2026:</span> AAA Law Intelligence (Beta)</li>
                <li><span style='color:#F2C678;'>2026 Q2:</span> AI Nodes — Personal Assistants</li>
                <li><span style='color:#F2C678;'>2026 Q3:</span> Secure Cloud Sync (Optional)</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # CTA BLOCK (DISABLED)
    # -------------------------------
    st.markdown(
        """
        <div style="
            background-color:#0B1523;
            border-radius:12px;
            padding:20px;
            margin-top:25px;
            text-align:center;
            border:1px dashed #2c3e50;
        ">
            <p style='color:#7f8c8d; font-size:15px;'>
                Premium Plans will be available soon.
            </p>
            <button disabled style="
                background-color:#1c2833;
                color:#6c7a89;
                padding:10px 20px;
                border:none;
                border-radius:8px;
                cursor:not-allowed;
                font-size:15px;
            ">Coming Soon</button>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
                "📊 Dashboard",
                "🩺 Health Log",
                "📥 Health Vault",
                "📁 Vault Manager",
                "🗑 Recycle Bin",
                "📄 PDF Preview",
                "🔍 OCR",
                "🧠 Summary (Demo)",
                "✨ Merged View",
                "🧬 Summary AI",
                "📊 Insights AI",
                "📚 Insights History",     # <— NEW, positioned after Insights AI
                "📘 Summary Report",
                "💎 Subscription Plans",
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

    elif choice == "💎 Subscription Plans":
        page_subscription_plans()

    elif choice == "🌟 Premium (Coming Soon)":
        page_premium()

    elif choice == "🧊 Snapshots":
        page_snapshots()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

