# ============================================================
# AAA — HEALTH INTELLIGENCE (MVP)
# FULL CLEAN REBUILD • LOGO FIX • FOOTER FIX • ALL MODULES
# ============================================================

import streamlit as st
import json
import os
import shutil
from datetime import datetime
from google import generativeai as genai
import fitz   # PyMuPDF for PDF rendering

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="💎 AAA — Health Intelligence (MVP)",
    page_icon="💎",
    layout="wide",
)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ============================================================
# HEADER + FOOTER
# ============================================================

def aaa_header():
    import streamlit as st
    import base64

    # Read the logo file in binary
    with open("assets/logo.png", "rb") as f:
        data = f.read()

    # Convert to base64 string
    encoded = base64.b64encode(data).decode()

    # Build HTML with embedded base64 image
    html = f"""
    <div style="width:100%; text-align:center; margin-top:10px;">
        <img src="data:image/png;base64,{encoded}" style="width:150px;">
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def aaa_footer():
    st.markdown(
        """
        <br><br>
        <div style="text-align:center; padding:25px;">
            <p style="color:#e2e8f0; font-size:24px; font-weight:700; margin:0;">
                Crafted with precision by <b>Rajdeep Singh</b> — Artigellence Augmentation Aggregator
            </p>
            <p style="color:#94a3b8; font-size:20px; margin-top:10px;">
                Powered by Edge-AI Orchestration Layer • Gemini • Vertex AI
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
# DIRECTORIES
# ============================================================

HEALTH_LOG_FILE = "health_log.json"
VAULT_DIR = "vault_files"
OCR_DATA_FILE = "ocr_results.json"
SNAPSHOT_DIR = "snapshots"
PHOTO_DIR = "photos"

for d in [VAULT_DIR, SNAPSHOT_DIR, PHOTO_DIR]:
    os.makedirs(d, exist_ok=True)


# ============================================================
# PAGE 1 — HEALTH LOG
# ============================================================

def page_health_log():
    aaa_header()
    st.subheader("🧿 Daily Health Log")

    date = st.date_input("Date")
    notes = st.text_area("Notes / Symptoms / Observations")

    if st.button("Save Entry"):
        log = load_json(HEALTH_LOG_FILE, [])
        log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": str(date),
            "notes": notes
        })
        save_json(HEALTH_LOG_FILE, log)
        st.success("Entry saved successfully!")

    st.write("### Previous Log Entries")
    log = load_json(HEALTH_LOG_FILE, [])
    for entry in reversed(log):
        with st.expander(f"{entry['date']}"):
            st.write(entry["notes"])

    aaa_footer()


# ============================================================
# PAGE 2 — HEALTH VAULT (Upload files)
# ============================================================

def page_vault():
    aaa_header()
    st.subheader("🗂️ Health Vault")

    uploaded = st.file_uploader("Upload Image/PDF", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded:
        save_path = os.path.join(VAULT_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"{uploaded.name} saved successfully!")

    st.write("### Stored Files")
    files = os.listdir(VAULT_DIR)
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
# PAGE 4 — OCR (Advanced)
# ============================================================

def page_ocr():
    aaa_header()
    st.subheader("🔍 Advanced OCR Extraction")

    file = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "pdf"])

    if file:
        st.info("Processing… 3–10 seconds…")

        temp_path = os.path.join(PHOTO_DIR, file.name)
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())

        extracted_text = ""

        # ------ PDF CASE ------
        if file.name.lower().endswith(".pdf"):
            doc = fitz.open(temp_path)
            st.write(f"Pages detected: {len(doc)}")

            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")

                st.write(f"Page {i+1}")

                response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                    ["Extract ALL text (no summary).", img_bytes]
                )

                extracted_text += f"\n\n--- PAGE {i+1} ---\n" + response.text

        # ------ Image case ------
        else:
            image_bytes = file.getvalue()
            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                ["Extract ALL text (no summary).", image_bytes]
            )
            extracted_text = response.text

        # Save OCR
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ocr_log = load_json(OCR_DATA_FILE, [])
        ocr_log.append({
            "timestamp": timestamp,
            "filename": file.name,
            "text": extracted_text
        })
        save_json(OCR_DATA_FILE, ocr_log)

        st.success("OCR Completed!")
        st.text_area("Extracted Text", extracted_text, height=300)

    # Show previous OCR
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
    path = os.path.join(SNAPSHOT_DIR, name)

    with open(path, "w") as f:
        json.dump(snap, f, indent=4)

    return name


def page_snapshots():
    aaa_header()
    st.subheader("📸 Data Snapshots")

    if st.button("💾 Create Snapshot"):
        name = save_snapshot()
        st.success(f"Snapshot saved: {name}")
        st.experimental_rerun()

    snaps = sorted(os.listdir(SNAPSHOT_DIR))

    if not snaps:
        st.info("No snapshots found.")
        aaa_footer()
        return

    for snap in snaps:
        with st.expander(snap):
            path = os.path.join(SNAPSHOT_DIR, snap)
            with open(path, "r") as f:
                data = json.load(f)
            st.json(data)

            c1, c2 = st.columns(2)

            with c1:
                if st.button(f"Restore {snap}", key=f"restore_{snap}"):
                    save_json(HEALTH_LOG_FILE, data["health_log"])
                    save_json(OCR_DATA_FILE, data["ocr"])
                    st.success("Snapshot restored.")
                    st.experimental_rerun()

            with c2:
                if st.button(f"Delete {snap}", key=f"delete_{snap}"):
                    os.remove(path)
                    st.warning("Snapshot deleted.")
                    st.experimental_rerun()

    aaa_footer()


# ============================================================
# PAGE 6 — SUMMARY AI
# ============================================================

def page_summary():
    aaa_header()
    st.subheader("🧠 AI Summary Report")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    log_choice = st.selectbox(
        "Select Health Log Entry",
        list(range(len(logs))),
        format_func=lambda i: logs[i]["date"] if logs else "None"
    ) if logs else None

    ocr_choice = st.selectbox(
        "Select OCR Extraction",
        list(range(len(ocr))),
        format_func=lambda i: ocr[i]["filename"] if ocr else "None"
    ) if ocr else None

    if st.button("Generate Summary"):
        parts = []

        if log_choice is not None:
            parts.append(f"HEALTH LOG:\n{logs[log_choice]}")

        if ocr_choice is not None:
            parts.append(f"OCR TEXT:\n{ocr[ocr_choice]['text']}")

        if not parts:
            st.error("Nothing selected.")
            return

        prompt = "\n\n".join(parts)

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"""
        Create a structured medical summary with:
        - Key symptoms
        - Risk markers
        - Trends
        - Patient-friendly explanation

        TEXT:
        {prompt}
        """)

        st.success("Summary generated.")
        st.markdown(response.text)

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
        st.info("No data found.")
        aaa_footer()
        return

    combined.sort(key=lambda x: x["timestamp"], reverse=True)

    for item in combined:
        with st.expander(f"{item['timestamp']} — {item['type']}"):
            st.write(item["content"])

    aaa_footer()


# ============================================================
# PAGE 8 — INSIGHTS AI
# ============================================================

def page_insights():
    aaa_header()
    st.subheader("📊 AI Pattern Insights")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    if not logs and not ocr:
        st.info("No data available yet.")
        aaa_footer()
        return

    data = {"logs": logs, "ocr": ocr}

    if st.button("Generate Insights"):
        prompt = f"""
        You are an AI medical insights engine.
        Analyze this data and find:
        - Trends
        - Risk patterns
        - Correlations
        - Anomalies
        - Helpful next steps

        DATA:
        {json.dumps(data, indent=2)}
        """

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        st.success("Insights generated.")
        st.write(response.text)

    aaa_footer()


# ============================================================
# NAVIGATION
# ============================================================

def main():
    st.sidebar.title("💎 AAA — Health Intelligence")

    pages = {
        "🧿 Health Log": page_health_log,
        "🗂️ Health Vault": page_vault,
        "📄 PDF Preview": page_pdf_preview,
        "🔍 OCR": page_ocr,
        "📸 Snapshots": page_snapshots,
        "🧠 Summary AI": page_summary,
        "🔗 Merged View": page_merged,
        "📊 Insights AI": page_insights,
    }

    choice = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[choice]()


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":
    main()
