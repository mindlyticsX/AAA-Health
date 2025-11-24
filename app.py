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
# DISCLAIMER (GLOBAL)
# ============================================================

def aaa_disclaimer():
    st.markdown("""
        <div style="
            margin-top: 40px;
            padding: 18px;
            background: rgba(15, 23, 42, 0.45);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.08);
            color: #e2e8f0;
            font-size: 13px;
            line-height: 1.5;
        ">
            <strong>Disclaimer:</strong><br>
            AAA-Health is an informational tool designed to help users organise,
            store, summarise, and understand their own health data.
            It does <strong>not</strong> diagnose, treat, or replace professional
            medical advice.<br><br>
            Always consult a qualified healthcare professional for any questions
            related to medical conditions or emergencies.
        </div>
    """, unsafe_allow_html=True)

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
# STEP 23 — MERGE HEALTH LOG + OCR RESULTS + VAULT FILES
# ============================================================

def merge_all_health_data():
    """
    Returns a unified merged structure combining:
    - Daily Health Log entries (health_log.json)
    - OCR extracted text results (ocr_data.json)
    - Raw file list from Vault directory
    """

    # ---- Load Health Log ----
    health_log = load_json(HEALTH_LOG_FILE, [])

    # ---- Load OCR Results ----
    ocr_results = load_json(OCR_DATA_FILE, [])

    # ---- Load Vault File List ----
    vault_files = []
    for f in os.listdir(VAULT_DIR):
        file_path = os.path.join(VAULT_DIR, f)
        if os.path.isfile(file_path):
            vault_files.append({
                "filename": f,
                "path": file_path,
                "timestamp": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).strftime("%Y-%m-%d %H:%M:%S")
            })

    # ---- Build Unified Structure ----
    merged = {
        "health_log": health_log,
        "ocr_results": ocr_results,
        "vault_files": vault_files,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return merged


# ============================================================
# STEP 24 — SNAPSHOTS (Create + Restore + List)
# ============================================================

def page_snapshots():

    aaa_header()
    st.subheader("🗂️ Snapshots — Full Backup & Restore")

    SNAPSHOT_DIR = "snapshots"
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    st.write("Create a full backup of:")
    st.write("- Health Log")
    st.write("- OCR Results")
    st.write("- Vault File List")
    st.write("- Generated timestamp")

    # --------------------------------------------------------
    # CREATE SNAPSHOT BUTTON
    # --------------------------------------------------------
    if st.button("📸 Create Snapshot"):
        try:
            # Build merged data
            merged = merge_all_health_data()

            # File name
            snap_name = datetime.now().strftime("snapshot_%Y%m%d_%H%M%S.json")
            snap_path = os.path.join(SNAPSHOT_DIR, snap_name)

            # Save snapshot
            with open(snap_path, "w") as f:
                json.dump(merged, f, indent=4)

            st.success(f"Snapshot saved: {snap_name}")

        except Exception as e:
            st.error(f"Snapshot failed: {e}")

    st.write("### Existing Snapshots")

    # --------------------------------------------------------
    # LIST SNAPSHOTS
    # --------------------------------------------------------
    files = sorted(os.listdir(SNAPSHOT_DIR))

    if not files:
        st.info("No snapshots available.")
        aaa_footer()
        return

    for f in files:
        snap_path = os.path.join(SNAPSHOT_DIR, f)

        with st.expander(f):

            # View snapshot JSON
            if st.button(f"🔍 View {f}", key=f"view_{f}"):
                try:
                    with open(snap_path, "r") as infile:
                        content = infile.read()
                    st.code(content, language="json")
                except Exception as e:
                    st.error(f"Error reading snapshot: {e}")

            # --------------------------------------------------------
            # RESTORE SNAPSHOT
            # --------------------------------------------------------
            if st.button(f"♻️ Restore {f}", key=f"restore_{f}"):
                try:
                    with open(snap_path, "r") as infile:
                        data = json.load(infile)

                    # Restore components
                    save_json(HEALTH_LOG_FILE, data.get("health_log", []))
                    save_json(OCR_DATA_FILE, data.get("ocr_results", []))

                    st.success("Snapshot restored successfully!")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Restore failed: {e}")

    aaa_footer()


# ============================================================
# DIRECTORIES (FINAL — REQUIRED FOR STEP-25)
# ============================================================

HEALTH_LOG_FILE = "health_log.json"
VAULT_DIR = "vault_files"
PHOTO_DIR = "photos"
SNAPSHOT_DIR = "snapshots"
OCR_DATA_FILE = "ocr_results.json"

# NEW: Required for Recycle Bin (Step 25)
RECYCLE_DIR = "recycle_bin"

# Create directories if missing
for d in [VAULT_DIR, PHOTO_DIR, SNAPSHOT_DIR, RECYCLE_DIR]:
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
# PAGE 2B — HEALTH VAULT MANAGER
# (Full Viewer + OCR + Summary AI + Delete + Rename)
# ============================================================

def page_vault_manager():
    aaa_header()
    st.subheader("📁 Health Vault Manager")

    files = os.listdir(VAULT_DIR)

    if not files:
        st.info("No files stored in Vault.")
        aaa_footer()
        return

    for file_name in files:
        file_path = os.path.join(VAULT_DIR, file_name)

        with st.expander(file_name):

            # ------------------------------------------------
            # PREVIEW: PDF
            # ------------------------------------------------
            if file_name.lower().endswith(".pdf"):
                try:
                    pdf = fitz.open(file_path)
                    total_pages = len(pdf)
                    st.write(f"PDF Pages: {total_pages}")

                    page_num = st.number_input(
                        f"Page number for {file_name}",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        step=1,
                        key=f"pg_{file_name}"
                    )

                    page = pdf[page_num - 1]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    st.image(pix.tobytes("png"), use_column_width=True)
                    pdf.close()
                except Exception as e:
                    st.error(f"Error previewing PDF: {e}")

            # ------------------------------------------------
            # PREVIEW: IMAGE
            # ------------------------------------------------
            elif file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_path, use_column_width=True)

            # ------------------------------------------------
            # STEP 21 — OCR (Extract Text)
            # ------------------------------------------------
            st.write("### 🔍 OCR (Extract Text)")

            if st.button(f"📄 Run OCR on {file_name}", key=f"ocr_{file_name}"):
                try:
                    st.info("Running OCR… please wait 3–8 seconds…")

                    extracted_text = ""

                    # ===== PDF CASE =====
                    if file_name.lower().endswith(".pdf"):
                        doc = fitz.open(file_path)
                        st.write(f"Pages detected: {len(doc)}")

                        for i, page in enumerate(doc):
                            pix = page.get_pixmap()
                            img_bytes = pix.tobytes("png")

                            response = genai.GenerativeModel(
                                "gemini-2.0-flash"
                            ).generate_content(
                                ["Extract ALL text (no summary).", img_bytes]
                            )

                            extracted_text += f"\n\n--- PAGE {i+1} ---\n{response.text}"

                    # ===== IMAGE CASE =====
                    else:
                        with open(file_path, "rb") as f:
                            img_bytes = f.read()

                        response = genai.GenerativeModel(
                            "gemini-2.0-flash"
                        ).generate_content(
                            ["Extract ALL text (no summary).", img_bytes]
                        )
                        extracted_text = response.text

                    # Save OCR to file
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ocr_log = load_json(OCR_DATA_FILE, [])
                    ocr_log.append({
                        "timestamp": timestamp,
                        "filename": file_name,
                        "text": extracted_text
                    })
                    save_json(OCR_DATA_FILE, ocr_log)

                    st.success("OCR Completed!")
                    st.text_area("Extracted Text", extracted_text, height=300)

                except Exception as e:
                    st.error(f"OCR failed: {e}")

            # ------------------------------------------------
            # STEP 22 — SUMMARY REPORT (NEW)
            # ------------------------------------------------
            st.write("### 🧠 Summary Report (AI Medical Summary)")

            if st.button(f"✨ Generate Summary for {file_name}", key=f"summ_{file_name}"):
                try:
                    st.info("Generating summary… please wait 3–6 seconds…")

                    summary_text = ""

                    # ===== PDF CASE =====
                    if file_name.lower().endswith(".pdf"):
                        doc = fitz.open(file_path)

                        for i, page in enumerate(doc):
                            pix = page.get_pixmap()
                            img_bytes = pix.tobytes("png")

                            response = genai.GenerativeModel(
                                "gemini-2.0-flash"
                            ).generate_content(
                                ["Summarize this medical document clearly for a patient:", img_bytes]
                            )

                            summary_text += f"\n\n--- PAGE {i+1} ---\n{response.text}"

                    # ===== IMAGE CASE =====
                    else:
                        with open(file_path, "rb") as f:
                            img_bytes = f.read()

                        response = genai.GenerativeModel(
                            "gemini-2.0-flash"
                        ).generate_content(
                            ["Summarize this medical image or report clearly for a patient:", img_bytes]
                        )
                        summary_text = response.text

                    # Save summary to summary_results.json
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    summ_log = load_json("summary_results.json", [])
                    summ_log.append({
                        "timestamp": timestamp,
                        "filename": file_name,
                        "summary": summary_text
                    })
                    save_json("summary_results.json", summ_log)

                    st.success("Summary Generated!")
                    st.text_area("Summary Report", summary_text, height=250)

                except Exception as e:
                    st.error(f"Summary generation failed: {e}")

            # ------------------------------------------------
            # DELETE BUTTON
            # ------------------------------------------------
            if st.button(f"🗑 Delete {file_name}", key=f"del_{file_name}"):
                try:
                    recycle_dir = "recycle_bin"
                    os.makedirs(recycle_dir, exist_ok=True)
                    shutil.move(file_path, os.path.join(recycle_dir, file_name))
                    st.success(f"{file_name} moved to Recycle Bin.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

            # ------------------------------------------------
            # RENAME BUTTON (STEP 20)
            # ------------------------------------------------
            ext = os.path.splitext(file_name)[1]

            new_base = st.text_input(
                f"Rename {file_name} (without extension)",
                value=os.path.splitext(file_name)[0],
                key=f"rename_input_{file_name}"
            )

            if st.button(f"✏️ Apply Rename for {file_name}", key=f"rename_btn_{file_name}"):
                if not new_base.strip():
                    st.error("File name cannot be empty.")
                else:
                    new_name = new_base.strip() + ext
                    new_path = os.path.join(VAULT_DIR, new_name)

                    if os.path.exists(new_path):
                        st.error("A file with this name already exists.")
                    else:
                        try:
                            os.rename(file_path, new_path)
                            st.success(f"Renamed to {new_name}")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Rename failed: {e}")

    aaa_footer()


# ============================================================
# STEP 25 — RECYCLE BIN (Viewer + Restore + Permanent Delete)
# ============================================================

def page_recycle_bin():
    aaa_header()
    st.subheader("🗑 Recycle Bin")

    recycle_dir = RECYCLE_DIR

    # Ensure folder exists
    os.makedirs(recycle_dir, exist_ok=True)

    files = os.listdir(recycle_dir)

    if not files:
        st.info("Recycle Bin is empty.")
        aaa_footer()
        return

    for f in files:
        file_path = os.path.join(recycle_dir, f)

        with st.expander(f):

            st.write(f"**File:** {f}")
            st.write(f"**Deleted On:** {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}")

            # Preview
            if f.lower().endswith(".pdf"):
                try:
                    pdf = fitz.open(file_path)
                    total_pages = len(pdf)

                    pg = st.number_input(
                        f"Preview Page (PDF) — {f}",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        step=1,
                        key=f"rb_pdf_{f}"
                    )

                    page = pdf[pg - 1]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    st.image(pix.tobytes("png"), use_column_width=True)
                    pdf.close()

                except Exception as e:
                    st.error(f"Error previewing PDF: {e}")

            elif f.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_path, use_column_width=True)

            # ------------------------------------------------
            # RESTORE FILE
            # ------------------------------------------------
            if st.button(f"♻️ Restore {f}", key=f"restore_rb_{f}"):
                try:
                    restored_path = os.path.join(VAULT_DIR, f)
                    shutil.move(file_path, restored_path)
                    st.success(f"{f} restored to Vault.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Restore failed: {e}")

            # ------------------------------------------------
            # PERMANENT DELETE
            # ------------------------------------------------
            if st.button(f"❌ Permanently Delete {f}", key=f"permdelete_rb_{f}"):
                try:
                    os.remove(file_path)
                    st.success(f"{f} permanently deleted.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")

    aaa_footer()


# ============================================================
# PAGE 3 — STEP 18: MULTI-PAGE PDF PREVIEW (REPLACEMENT BLOCK)
# ============================================================
import fitz  # PyMuPDF

def page_pdf_preview():
    aaa_header()
    st.subheader("📄 PDF Preview")

    # List PDFs in vault
    pdfs = [f for f in os.listdir(VAULT_DIR) if f.lower().endswith(".pdf")]

    if not pdfs:
        st.info("No PDF files found in Vault.")
        aaa_footer()
        return

    selected_pdf = st.selectbox("Select a PDF", pdfs)
    pdf_path = os.path.join(VAULT_DIR, selected_pdf)

    try:
        pdf = fitz.open(pdf_path)
        total_pages = len(pdf)

        st.write(f"Total pages: **{total_pages}**")

        # Page number selector
        page_number = st.number_input(
            "Page number",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1
        )

        # Render page
        page = pdf[page_number - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High-quality
        img_bytes = pix.tobytes("png")

        st.image(img_bytes, use_column_width=True, caption=f"Page {page_number}")

        pdf.close()

    except Exception as e:
        st.error(f"Failed to load PDF: {e}")

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
# STEP 26 — HEALTH INSIGHTS (AI SUMMARY OF ALL DATA)
# ============================================================

def page_insights():
    aaa_header()
    st.subheader("🧠 Insights AI")

    st.info("This page analyses your full health data — logs, OCR text, and Vault files — and generates personalised insights.")

    # ---- Load merged data ----
    merged_data = merge_all_health_data()

    if not merged_data:
        st.warning("No data found to analyse.")
        return

    if st.button("✨ Generate AI Insights"):
        try:
            with st.spinner("Analysing your health profile… 4–10 seconds…"):
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content([
                    "You are a medical assistant. Analyse the user's FULL health dataset and give structured insights. "
                    "Return clear sections: Summary, Key Issues, Red Flags, Recommendations, Diet, Sleep, Mental Health, "
                    "Follow-up tests. Use simple language. If data is incomplete, still generate helpful insights.",
                    json.dumps(merged_data)
                ])

            insights_text = response.text

            st.success("Insights generated successfully!")
            st.markdown(insights_text)

        except Exception as e:
            st.error(f"AI Insights failed: {e}")


# ============================================================
# STEP 28 — SUMMARY REPORT (AUTO PDF GENERATION)
# ============================================================

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def generate_summary_pdf(merged_data, output_path="summary_report.pdf"):
    try:
        c = canvas.Canvas(output_path, pagesize=letter)

        # ----- Title -----
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, 10.5 * inch, "AAA – Health Summary Report")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 10.1 * inch, f"Generated At: {merged_data.get('generated_at', '')}")

        # ----- Section: Health Log Count -----
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, 9.6 * inch, "1. Health Log Overview")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 9.35 * inch, f"Total Log Entries: {len(merged_data.get('health_log', []))}")

        # ----- Section: OCR Count -----
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, 8.8 * inch, "2. OCR / Extracted Text")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 8.55 * inch, f"OCR Extracted Files: {len(merged_data.get('ocr_results', []))}")

        # ----- Section: Vault Files -----
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, 8.05 * inch, "3. Vault Files Uploaded")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 7.8 * inch, f"Total Files in Vault: {len(merged_data.get('vault_files', []))}")

        # ----- Footer -----
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1 * inch, 1 * inch,
                     "Crafted with precision by Rajdeep Singh — Artigellence Augmentation Aggregator")

        c.drawString(1 * inch, 0.8 * inch,
                     "Powered by Edge-AI Orchestration Layer • Gemini • Vertex AI")

        c.save()
        return True

    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        return False


def page_summary_report():
    aaa_header()
    st.subheader("📄 Summary Report (PDF)")

    st.info("This generates a quick PDF report combining logs, OCR and Vault file overview.")

    merged = merge_all_health_data()

    if st.button("📥 Generate Summary PDF"):
        ok = generate_summary_pdf(merged)
        if ok:
            st.success("Summary PDF generated successfully!")
            with open("summary_report.pdf", "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=f,
                    file_name="AAA_Summary_Report.pdf",
                    mime="application/pdf"
                )


# ============================================================
# MAIN APP ENTRY
# ============================================================

def main():
    st.sidebar.title("💎 AAA — Health Intelligence")

    pages = {
        "📘 Health Log": page_health_log,
        "📁 Health Vault": page_vault,
        "📄 PDF Preview": page_pdf_preview,
        "🔍 OCR": page_ocr,
        "🗂 Snapshots": page_snapshots,
        "🧠 Summary AI": page_summary,
        "📊 Merged View": page_merged,
        "🔮 Insights AI": page_insights,
        "📂 Vault Manager": page_vault_manager,
        "🗑 Recycle Bin": page_recycle_bin,
        "Summary Report (PDF)": page_summary_report,
    }

    choice = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[choice]()  # Run selected page

    # Only ONE footer + disclaimer
    aaa_disclaimer()
    aaa_footer()

