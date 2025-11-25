# ============================================================
# AAA — HEALTH INTELLIGENCE (MVP • CLEAN VERSION • FINAL)
# ============================================================

import streamlit as st
import json
import os
import shutil
from datetime import datetime
from google import generativeai as genai
import fitz   # PyMuPDF for PDF rendering
import base64
from fpdf import FPDF

# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="💎 AAA — Health Intelligence",
    page_icon="💎",
    layout="wide",
)

# GEMINI API KEY
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ============================================================
# DIRECTORIES
# ============================================================

HEALTH_LOG_FILE = "health_log.json"
VAULT_DIR = "vault_files"
OCR_DATA_FILE = "ocr_results.json"
SNAPSHOT_DIR = "snapshots"
PHOTO_DIR = "photos"
RECYCLE_BIN_DIR = "recycle_bin"

for d in [VAULT_DIR, SNAPSHOT_DIR, PHOTO_DIR, RECYCLE_BIN_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# HEADER + FOOTER (FINAL DISCLAIMER)
# ============================================================

FINAL_DISCLAIMER = """
AAA — Health Intelligence provides AI-assisted insights.
It does not replace professional medical, financial or legal advice.
Always consult certified experts for critical decisions.
"""

def aaa_header():
    st.markdown("<br>", unsafe_allow_html=True)
    logo_path = "assets/logo.png"

    if os.path.exists(logo_path):
        st.image(logo_path, width=130)
    else:
        st.warning("⚠️ Missing: assets/logo.png")

    st.markdown("<br>", unsafe_allow_html=True)


def aaa_footer():
    st.markdown(
        f"""
        <br><br>
        <div style="
            background:rgba(148,163,184,0.10);
            padding:20px 24px;
            border-radius:12px;
            max-width:850px;
            margin:0 auto 30px auto;
            text-align:center;
            line-height:1.6;
        ">
            <p style="color:#e2e8f0; font-size:15px; margin:0;">
                {FINAL_DISCLAIMER}
            </p>
        </div>

        <div style="text-align:center; padding:25px;">
            <p style="color:#e2e8f0; font-size:22px; font-weight:700; margin:0;">
                Crafted by <b>Rajdeep Singh</b> — Artigellence Augmentation Aggregator
            </p>
            <p style="color:#94a3b8; font-size:18px; margin-top:10px;">
                Edge-AI Orchestration Layer • Gemini • Vertex AI
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# ============================================================
# PAGE 1 — HEALTH LOG
# ============================================================

def page_health_log():
    aaa_header()
    st.subheader("🧿 Daily Health Log")

    date = st.date_input("Date")
    notes = st.text_area("Notes / Symptoms / Observations", height=150)

    if st.button("Save Entry"):
        log = load_json(HEALTH_LOG_FILE, [])
        log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": str(date),
            "notes": notes
        })
        save_json(HEALTH_LOG_FILE, log)
        st.success("Entry saved successfully!")

    st.write("### Previous Entries")
    for entry in reversed(load_json(HEALTH_LOG_FILE, [])):
        with st.expander(f"{entry['date']}"):
            st.write(entry["notes"])

    aaa_footer()

# ============================================================
# PAGE 2 — HEALTH VAULT
# ============================================================

def page_vault():
    aaa_header()
    st.subheader("🗂️ Health Vault")

    uploaded = st.file_uploader("Upload Image/PDF", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded:
        save_path = os.path.join(VAULT_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"{uploaded.name} saved!")

    files = os.listdir(VAULT_DIR)
    st.write("### Stored Files")

    if not files:
        st.info("No files uploaded yet.")
    else:
        for f in files:
            st.write(f)

    aaa_footer()

# ============================================================
# PAGE 3 — PDF PREVIEW
# ============================================================

def page_pdf_preview():
    aaa_header()
    st.subheader("📄 PDF Preview")

    pdfs = [f for f in os.listdir(VAULT_DIR) if f.lower().endswith(".pdf")]

    if not pdfs:
        st.info("No PDF files found.")
        aaa_footer()
        return

    selected = st.selectbox("Select PDF", pdfs)
    pdf_path = os.path.join(VAULT_DIR, selected)

    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            st.image(pix.tobytes(), caption=f"Page {i+1}", use_container_width=True)
    except:
        st.error("Failed to load PDF.")

    aaa_footer()

# ============================================================
# PAGE 4 — OCR (Gemini)
# ============================================================

def page_ocr():
    aaa_header()
    st.subheader("🔍 OCR Extraction (Gemini)")

    file = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "pdf"])

    if file:
        st.info("Processing…")

        temp_path = os.path.join(PHOTO_DIR, file.name)
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())

        extracted_text = ""

        if file.name.lower().endswith(".pdf"):
            doc = fitz.open(temp_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                    ["Extract ALL text. No summary.", img_bytes]
                )
                extracted_text += f"\n\n--- PAGE {i+1} ---\n" + response.text
        else:
            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                ["Extract ALL text. No summary.", file.getvalue()]
            )
            extracted_text = response.text

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ocr_log = load_json(OCR_DATA_FILE, [])
        ocr_log.append({
            "timestamp": timestamp,
            "filename": file.name,
            "text": extracted_text
        })
        save_json(OCR_DATA_FILE, ocr_log)

        st.success("OCR Complete!")
        st.text_area("Extracted Text", extracted_text, height=300)

    st.write("### Previous OCR Results")
    for entry in load_json(OCR_DATA_FILE, []):
        with st.expander(f"{entry['timestamp']} — {entry['filename']}"):
            st.text(entry["text"])

    aaa_footer()

# ============================================================
# PAGE 5 — SNAPSHOTS
# ============================================================

def save_snapshot():
    snap = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "health_log": load_json(HEALTH_LOG_FILE, []),
        "ocr": load_json(OCR_DATA_FILE, []),
    }
    name = f"snapshot_{snap['timestamp'].replace(':','-').replace(' ','_')}.json"
    with open(os.path.join(SNAPSHOT_DIR, name), "w") as f:
        json.dump(snap, f, indent=4)
    return name

def page_snapshots():
    aaa_header()
    st.subheader("📸 Snapshots")

    if st.button("💾 Create Snapshot"):
        name = save_snapshot()
        st.success(f"Snapshot saved: {name}")
        st.experimental_rerun()

    snaps = sorted(os.listdir(SNAPSHOT_DIR))
    if not snaps:
        st.info("No snapshots.")
        aaa_footer()
        return

    for snap in snaps:
        with st.expander(snap):
            path = os.path.join(SNAPSHOT_DIR, snap)
            data = load_json(path, {})

            st.json(data)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Restore {snap}", key=f"rs_{snap}"):
                    save_json(HEALTH_LOG_FILE, data["health_log"])
                    save_json(OCR_DATA_FILE, data["ocr"])
                    st.success("Restored!")
                    st.experimental_rerun()

            with col2:
                if st.button(f"Delete {snap}", key=f"del_{snap}"):
                    os.remove(path)
                    st.warning("Deleted!")
                    st.experimental_rerun()

    aaa_footer()

# ============================================================
# GLOBAL AI SUMMARY STATE (Shared Page-6 <-> Page-9)
# ============================================================

if "ai_summary" not in st.session_state:
    st.session_state["ai_summary"] = ""

def save_ai_summary(text: str):
    if text and isinstance(text, str) and text.strip():
        st.session_state["ai_summary"] = text

def get_ai_summary() -> str:
    val = st.session_state.get("ai_summary", "")
    return val if isinstance(val, str) else ""

# ============================================================
# PAGE 6 — AI SUMMARY
# ============================================================

def page_summary():
    aaa_header()
    st.subheader("🧠 AI Summary")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    log_choice = st.selectbox(
        "Select Health Log",
        list(range(len(logs))),
        format_func=lambda i: logs[i]["date"]
    ) if logs else None

    ocr_choice = st.selectbox(
        "Select OCR Entry",
        list(range(len(ocr))),
        format_func=lambda i: ocr[i]["filename"]
    ) if ocr else None

    if st.button("Generate Summary"):
        if log_choice is None and ocr_choice is None:
            st.error("Please select at least one.")
            return

        parts = []
        if log_choice is not None:
            parts.append(f"HEALTH LOG:\n{logs[log_choice]}")
        if ocr_choice is not None:
            parts.append(f"OCR:\n{ocr[ocr_choice]['text']}")

        prompt = "\n\n".join(parts)

        response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
            f"""
Convert the following into a clean, structured medical summary.

### 🧠 Medical Summary  
**Date:** (Infer from data)

---

### 1. Key Symptoms  
• ...

### 2. Risk Markers  
• ...

### 3. Trends  
• ...

### 4. Observations from OCR  
• ...

### 5. Recommendations  
• ...

RAW TEXT:
{prompt}
            """
        )

        st.success("Summary Ready")

        st.markdown("""
        <div style="
            background:rgba(255,255,255,0.04);
            padding:20px;
            border-radius:12px;
            border:1px solid rgba(255,255,255,0.08);
            box-shadow:0 4px 12px rgba(0,0,0,0.35);
        ">
        """, unsafe_allow_html=True)

        st.markdown(response.text)
        st.markdown("</div>", unsafe_allow_html=True)

        save_ai_summary(response.text)

    aaa_footer()

# ============================================================
# PAGE 7 — MERGED VIEW
# ============================================================

def page_merged():
    aaa_header()
    st.subheader("🔗 Unified Merged View")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    combined = []

    for x in logs:
        combined.append({
            "timestamp": x["timestamp"],
            "type": "Health Log",
            "content": x["notes"]
        })

    for x in ocr:
        combined.append({
            "timestamp": x["timestamp"],
            "type": f"OCR: {x['filename']}",
            "content": x["text"]
        })

    if not combined:
        st.info("No data available.")
        aaa_footer()
        return

    combined.sort(key=lambda x: x["timestamp"], reverse=True)

    for item in combined:
        with st.expander(f"{item['timestamp']} — {item['type']}"):
            st.write(item["content"])

    aaa_footer()

# ============================================================
# PAGE 8 — AI INSIGHTS
# ============================================================

def page_insights():
    aaa_header()
    st.subheader("📊 AI Insights")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    if st.button("Generate Insights"):
        combined = []

        for l in logs:
            combined.append(f"[Health Log] {l['date']}: {l['notes']}")

        for o in ocr:
            combined.append(f"[OCR] {o['timestamp']}: {o['text']}")

        prompt = f"""
You are a medical insights engine.
Analyze the following and extract:

1. Patterns & Trends
2. Correlations
3. Risks
4. Recommended Actions

DATA:
{combined}
"""

        response = genai.GenerativeModel("gemini-2.0-flash").generate_content(prompt)

        st.session_state["insights_result"] = response.text
        st.success("Insights Ready")

    result = st.session_state.get("insights_result", "")
    if result:
        st.markdown(result)

    aaa_footer()

# ============================================================
# PAGE 9 — SUMMARY REPORT (PDF EXPORT)
# ============================================================

def create_pdf_report(summary_text, logs, ocr):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 20)
    pdf.multi_cell(0, 12, "AAA — Health Intelligence Report")
    pdf.ln(4)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.ln(6)

    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 10, "AI Summary")
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 7, summary_text)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 10, "Health Logs")
    pdf.set_font("Arial", "", 12)

    for entry in logs:
        pdf.multi_cell(0, 7, f"{entry['date']} — {entry['notes']}")
        pdf.ln(2)

    pdf.ln(4)

    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 10, "OCR Extracted Text")
    pdf.set_font("Arial", "", 12)

    for entry in ocr:
        pdf.multi_cell(0, 7, f"{entry['filename']}:\n{entry['text']}")
        pdf.ln(3)

    return pdf.output(dest="S").encode("latin-1")


def page_summary_report():
    aaa_header()
    st.subheader("📘 Summary Report (PDF)")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])
    summary = get_ai_summary()

    st.markdown("### 🧠 AI Summary")
    st.markdown(summary if summary else "No summary generated yet.")

    if st.button("⬇️ Export Full PDF Report"):
        pdf_bytes = create_pdf_report(summary, logs, ocr)
        b64 = base64.b64encode(pdf_bytes).decode()

        href = f"""
        <a href="data:application/octet-stream;base64,{b64}" download="AAA_Health_Report.pdf">
        <button style="
            background:#0284c7;
            color:white;
            padding:12px 24px;
            border-radius:8px;
            border:none;
            cursor:pointer;">
            Download PDF
        </button>
        </a>
        """

        st.markdown(href, unsafe_allow_html=True)

    aaa_footer()

# ============================================================
# PAGE B1 — VAULT MANAGER PRO
# ============================================================

def file_metadata(path):
    stat = os.stat(path)
    size_kb = round(stat.st_size / 1024, 2)
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return size_kb, modified

def page_vault_manager():
    aaa_header()
    st.subheader("🗂️ Vault Manager Pro")

    files = [f for f in os.listdir(VAULT_DIR) if os.path.isfile(os.path.join(VAULT_DIR, f))]

    if not files:
        st.info("Nothing in Vault.")
        aaa_footer()
        return

    for f in files:
        path = os.path.join(VAULT_DIR, f)
        size_kb, modified = file_metadata(path)

        with st.expander(f"{f} — {size_kb} KB"):
            st.write(f"📅 Modified: {modified}")

            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(path, use_container_width=True)

            if f.lower().endswith(".pdf"):
                try:
                    doc = fitz.open(path)
                    page = doc.load_page(0)
                    pix = page.get_pixmap()
                    st.image(pix.tobytes(), caption="Page 1", use_container_width=True)
                except:
                    st.warning("Cannot preview PDF.")

            st.write("---")

            new_name = st.text_input(f"Rename {f}", value=f, key=f"rename_{f}")
            if st.button(f"Apply Rename for {f}", key=f"btn_{f}"):
                os.rename(path, os.path.join(VAULT_DIR, new_name))
                st.success("Renamed!")
                st.experimental_rerun()

            if st.button(f"Delete {f}", key=f"del_{f}"):
                trash_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}__{f}"
                shutil.move(path, os.path.join(RECYCLE_BIN_DIR, trash_name))
                st.warning(f"Moved to Recycle Bin as {trash_name}")
                st.experimental_rerun()

    aaa_footer()

# ============================================================
# PAGE — RECYCLE BIN
# ============================================================

def restore_from_recycle_bin(name):
    shutil.move(os.path.join(RECYCLE_BIN_DIR, name), os.path.join(VAULT_DIR, name))

def delete_permanently(name):
    os.remove(os.path.join(RECYCLE_BIN_DIR, name))

def page_recycle_bin():
    aaa_header()
    st.subheader("🗑 Recycle Bin")

    files = os.listdir(RECYCLE_BIN_DIR)

    if not files:
        st.info("Recycle Bin empty.")
        aaa_footer()
        return

    for f in files:
        path = os.path.join(RECYCLE_BIN_DIR, f)
        size_kb, modified = file_metadata(path)

        with st.expander(f"{f} — {size_kb} KB"):
            st.write(f"📅 Modified: {modified}")

            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(path, use_container_width=True)

            if f.lower().endswith(".pdf"):
                try:
                    doc = fitz.open(path)
                    page = doc.load_page(0)
                    pix = page.get_pixmap()
                    st.image(pix.tobytes(), caption="Page 1", use_container_width=True)
                except:
                    st.warning("Cannot preview PDF.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"♻ Restore {f}", key=f"rs_{f}"):
                    restore_from_recycle_bin(f)
                    st.success("Restored!")
                    st.experimental_rerun()

            with col2:
                if st.button(f"❌ Delete Permanently {f}", key=f"dp_{f}"):
                    delete_permanently(f)
                    st.warning("Deleted permanently.")
                    st.experimental_rerun()

    aaa_footer()

# ============================================================
# NAVIGATION
# ============================================================

def main():
    st.sidebar.title("💎 AAA — Health Intelligence")

    pages = {
        "🧿 Health Log": page_health_log,
        "🗂 Health Vault": page_vault,
        "📁 Vault Manager": page_vault_manager,
        "📄 PDF Preview": page_pdf_preview,
        "🔍 OCR": page_ocr,
        "📸 Snapshots": page_snapshots,
        "🧠 Summary AI": page_summary,
        "🔗 Merged View": page_merged,
        "📊 Insights AI": page_insights,
        "📘 Summary Report": page_summary_report,
        "🗑 Recycle Bin": page_recycle_bin,
    }

    choice = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[choice]()

# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":
    main()
