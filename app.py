# ============================================================
# AAA — HEALTH INTELLIGENCE (DEV VERSION)
# FULL CLEAN IMPORT BLOCK + STRIPE + MONETIZATION READY
# ============================================================

import streamlit as st
import json
import os
import shutil
from datetime import datetime
from google import generativeai as genai
import fitz        # PyMuPDF for PDF rendering
import base64
from fpdf import FPDF
import stripe      # Stripe for checkout sessions

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
# STRIPE CONFIG (PLACEHOLDERS - WIRED LATER)
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
        # For images, just store a placeholder - real OCR is done elsewhere
        text_chunks.append("Image file uploaded. OCR text is stored separately.")
    return "\n".join(text_chunks)

# ============================================================
# GEMINI - GENERIC CALLER
# ============================================================

def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key is missing. Please configure it in Streamlit secrets."

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
    page_title="AAA — Health Intelligence (DEV)",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(APP_CSS, unsafe_allow_html=True)

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
# PAGE 7 — MERGED VIEW (LOCKED)
# ============================================================

def page_merged():
    aaa_header()
    st.subheader("✨ Merged View (Doctor + Lab + Notes)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.info("Premium merged view will combine doctor notes, lab reports and personal logs into one layout.")
    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 8 — SUMMARY AI (PREMIUM FEATURE)
# ============================================================

def page_summary_ai():
    aaa_header()
    st.subheader("🧬 Summary AI (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            Generate an intelligent medical summary from your uploaded PDF,
            images, lab reports, and prescriptions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    if not files:
        st.warning("Upload files in the Vault to generate summaries.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select a file to summarize:", files)

    if st.button("Generate Summary"):
        with st.spinner("Analyzing with AAA Intelligence…"):
            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)
                prompt = f"Give a clear, patient-friendly medical summary for:\n\n{text[:4000]}"
                result = call_gemini(prompt)
                st.success("Summary generated!")
                st.write(result)
            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 9 — INSIGHTS AI (PREMIUM FEATURE)
# ============================================================

def page_insights_ai():
    aaa_header()
    st.subheader("📊 Insights AI (Premium)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    st.markdown(
        """
        <div style="font-size:16px; line-height:1.6; margin-bottom:15px;">
            Deep medical insight analysis including trends, risks, anomalies,
            and personalized recommendations.
        </div>
        """,
        unsafe_allow_html=True,
    )

    files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]
    if not files:
        st.warning("No files found in Vault.")
        monetization_cta()
        aaa_footer()
        return

    selected_file = st.selectbox("Select file for insights:", files)

    if st.button("Generate Insights"):
        with st.spinner("Extracting insights using AAA Intelligence…"):
            try:
                path = os.path.join(VAULT_DIR, selected_file)
                text = extract_text_any(path)
                prompt = (
                    "Provide detailed medical insights, anomalies, indicators, "
                    "and actionable recommendations based on:\n\n"
                    f"{text[:4000]}"
                )
                result = call_gemini(prompt)
                st.success("Insights generated!")
                st.write(result)
            except Exception as e:
                st.error(f"Error: {e}")

    monetization_cta()
    aaa_footer()

# ============================================================
# PAGE 10 — SUMMARY REPORT (PDF EXPORT)
# ============================================================

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "AAA — Health Intelligence Summary Report", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "AAA — Health Intelligence (Early Access)", 0, 0, "C")

def generate_summary_pdf(text: str, output_path: str):
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in text.split("\n"):
        pdf.multi_cell(0, 6, line)
    pdf.output(output_path)

def page_summary_report():
    aaa_header()
    st.subheader("📘 Summary Report (PDF)")

    if not is_premium():
        feature_locked()
        aaa_footer()
        return

    ai_summaries = load_json(AI_SUMMARY_FILE, [])
    if not ai_summaries:
        st.info("No AI summaries found. Generate some first in Summary AI.")
        aaa_footer()
        return

    options = [f"{i+1}. {s['date']} — {s.get('title','Summary')}" for i, s in enumerate(ai_summaries)]
    idx = st.selectbox("Choose a summary to export:", list(range(len(options))), format_func=lambda i: options[i])

    if st.button("Generate PDF Report"):
        summary_text = ai_summaries[idx]["text"]
        generate_summary_pdf(summary_text, SUMMARY_REPORT_PDF)
        st.success("PDF report generated.")

        with open(SUMMARY_REPORT_PDF, "rb") as f:
            st.download_button("Download Report", f, file_name="aaa_health_summary_report.pdf")

    monetization_cta()
    aaa_footer()

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
# PAGE 11 — SUBSCRIPTION PLANS (STRIPE PLACEHOLDER)
# ============================================================

def page_subscription_plans():
    aaa_header()
    st.subheader("💎 AAA Subscription Plans")

    st.markdown(
        """
        AAA Health gives you intelligent summaries of your medical files, personalized dashboards,
        snapshots, recycle-bin safety, and continuous updates.

        Below are the launch subscription options available for early users (5th Dec 2025).
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Free Tier")
    st.markdown(
        """
        - Upload & store your PDFs/images  
        - Basic Vault Manager  
        - Basic Health Log entry  
        - Limited AI summaries  
        - Standard dashboard  
        """,
    )

    st.markdown("### Premium — A$10 / month")
    st.markdown(
        """
        - Unlimited AI summaries  
        - Smart Dashboard + Tailored Health Indicators  
        - Priority OCR + Advanced Extraction  
        - Snapshot & Restore  
        - Early Access Features  
        - Support Circle (Trusted Family Access)  
        """,
    )

    st.markdown("### Premium India — ₹100 / month")
    st.markdown(
        """
        - Unlimited AI summaries  
        - Smart Dashboard + Tailored Indicators  
        - OCR Boost + Fast Processing  
        - Family/Support Circle  
        - Continuous Updates  
        """,
    )

    st.markdown("### US / International — $10 / month")
    st.markdown(
        """
        - Unlimited AI summaries  
        - Advanced Insights + Highlight Extraction  
        - Medical Frequency Insights (Serene Frequency)  
        - Snapshot & Restore  
        - Early Access to AAA Finance + Law (2026)  
        """,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("Upgrade A$10", use_container_width=True)
    with c2:
        st.button("Upgrade ₹100", use_container_width=True)
    with c3:
        st.button("Upgrade $10", use_container_width=True)
    with c4:
        st.button("Checkout coming soon…", use_container_width=True)

    aaa_footer()

# ============================================================
# MAIN NAVIGATION
# ============================================================

def main():
    mode = get_mode()  # ensures sidebar radio is rendered

    with st.sidebar:
        st.markdown("### 💎 AAA — Health Intelligence (DEV)")
        # Removed the extra duplicated "Navigate:" line here

    pages = {
        "🩺 Health Log": page_health_log,
        "📥 Health Vault": page_health_vault,
        "📁 Vault Manager": page_vault_manager,
        "🗑 Recycle Bin": page_recycle_bin,
        "📄 PDF Preview": page_pdf_preview,
        "🔍 OCR": page_ocr,
        "🧠 Summary (Demo)": page_summary,
        "✨ Merged View": page_merged,
        "🧬 Summary AI": page_summary_ai,
        "📊 Insights AI": page_insights_ai,
        "📘 Summary Report": page_summary_report,
        "💎 Subscription Plans": page_subscription_plans,
        "🧊 Snapshots": page_snapshots,
    }

    choice = st.sidebar.radio("Navigate:", list(pages.keys()))
    pages[choice]()

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
