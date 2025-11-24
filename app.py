# ============================================================
# AAA — HEALTH INTELLIGENCE (FINAL CLEAN VERSION)
# Footer only once (global). No duplicates.
# ============================================================

import streamlit as st
import json
import os
import shutil
from datetime import datetime
from google import generativeai as genai
import fitz  # PyMuPDF


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
    import base64
    with open("assets/logo.png", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="width:100%; text-align:center; margin-top:10px;">
            <img src="data:image/png;base64,{encoded}" style="width:150px;">
        </div>
        """,
        unsafe_allow_html=True
    )


def aaa_footer():
    st.markdown(
        """
        <br><br>
        <div style="text-align:center; padding:25px;">
            <p style="color:#e2e8f0; font-size:22px; font-weight:700; margin:0;">
                Crafted with precision by <b>Rajdeep Singh</b> — Artigellence Augmentation Aggregator
            </p>
            <p style="color:#94a3b8; font-size:18px; margin-top:10px;">
                Powered by Edge-AI Orchestration Layer • Gemini • Vertex AI
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DISCLAIMER
# ============================================================

def aaa_disclaimer():
    with st.expander("🔒 Legal · Privacy · Consent"):
        st.markdown(
            """
            **1. Health Disclaimer**  
            AAA-Health helps users organise, store and understand their
            personal health information. It does **NOT** diagnose, predict,
            or replace professional medical advice.  
            Always consult a qualified healthcare provider for any concern.

            ---

            **2. Privacy & Data Ownership**  
            • All uploaded files, logs and summaries stay fully under the user's control.  
            • Nothing is shared with any third party.  
            • Edge-AI models process your data but **do not store** anything.  
            • You may delete or restore your data at any time.

            ---

            **3. Consent**  
            By using AAA-Health, you agree to responsibly review your
            own records, and treat AI-generated summaries as supportive
            information only.
            """
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
# CONSTANTS + DIRECTORIES
# ============================================================

HEALTH_LOG_FILE = "health_log.json"
OCR_DATA_FILE = "ocr_results.json"
VAULT_DIR = "vault_files"
PHOTO_DIR = "photos"
SNAPSHOT_DIR = "snapshots"
RECYCLE_DIR = "recycle_bin"

for d in [VAULT_DIR, PHOTO_DIR, SNAPSHOT_DIR, RECYCLE_DIR]:
    os.makedirs(d, exist_ok=True)


# ============================================================
# MERGE HEALTH DATA
# ============================================================

def merge_all_health_data():
    health_log = load_json(HEALTH_LOG_FILE, [])
    ocr_results = load_json(OCR_DATA_FILE, [])

    vault_files = []
    for f in os.listdir(VAULT_DIR):
        file_path = os.path.join(VAULT_DIR, f)
        if os.path.isfile(file_path):
            vault_files.append({
                "filename": f,
                "path": file_path,
                "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
            })

    return {
        "health_log": health_log,
        "ocr_results": ocr_results,
        "vault_files": vault_files,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# ============================================================
# PAGE FUNCTIONS (NO FOOTERS INSIDE)
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
        with st.expander(entry["date"]):
            st.write(entry["notes"])


def page_vault():
    aaa_header()
    st.subheader("📁 Health Vault")

    uploaded = st.file_uploader("Upload Image/PDF", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded:
        save_path = os.path.join(VAULT_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"{uploaded.name} saved!")

    st.write("### Stored Files")
    files = os.listdir(VAULT_DIR)
    if not files:
        st.info("No files yet.")
    else:
        for f in files:
            st.write(f)


def page_vault_manager():
    aaa_header()
    st.subheader("📂 Vault Manager")

    files = os.listdir(VAULT_DIR)
    if not files:
        st.info("No stored files.")
        return

    for file_name in files:
        file_path = os.path.join(VAULT_DIR, file_name)

        with st.expander(file_name):

            # PDF Preview
            if file_name.lower().endswith(".pdf"):
                try:
                    pdf = fitz.open(file_path)
                    total_pages = len(pdf)
                    st.write(f"PDF Pages: {total_pages}")

                    pg = st.number_input(
                        f"Page for {file_name}",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        step=1,
                        key=f"pg_{file_name}"
                    )
                    page = pdf[pg - 1]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    st.image(pix.tobytes("png"), use_column_width=True)
                    pdf.close()
                except Exception as e:
                    st.error(f"Preview error: {e}")

            # Image Preview
            elif file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_path, use_column_width=True)

            # OCR
            st.write("### 🔍 OCR")
            if st.button(f"Run OCR on {file_name}", key=f"ocr_{file_name}"):
                try:
                    extracted = ""

                    if file_name.lower().endswith(".pdf"):
                        doc = fitz.open(file_path)
                        for i, page in enumerate(doc):
                            pix = page.get_pixmap()
                            img = pix.tobytes("png")
                            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                                ["Extract ALL text.", img]
                            )
                            extracted += f"\n\n--- PAGE {i+1} ---\n{response.text}"

                    else:
                        with open(file_path, "rb") as f:
                            img = f.read()
                        response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                            ["Extract ALL text.", img]
                        )
                        extracted = response.text

                    ocr_log = load_json(OCR_DATA_FILE, [])
                    ocr_log.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "filename": file_name,
                        "text": extracted
                    })
                    save_json(OCR_DATA_FILE, ocr_log)

                    st.success("OCR completed!")
                    st.text_area("Extracted Text", extracted, height=250)

                except Exception as e:
                    st.error(f"OCR failed: {e}")

            # Summary
            st.write("### 🧠 Summary")
            if st.button(f"Generate Summary for {file_name}", key=f"summ_{file_name}"):
                try:
                    summary = ""

                    if file_name.lower().endswith(".pdf"):
                        doc = fitz.open(file_path)
                        for i, page in enumerate(doc):
                            pix = page.get_pixmap()
                            img = pix.tobytes("png")
                            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                                ["Summarize clearly for patient:", img]
                            )
                            summary += f"\n\n--- PAGE {i+1} ---\n{response.text}"

                    else:
                        with open(file_path, "rb") as f:
                            img = f.read()
                        response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                            ["Summarize clearly for patient:", img]
                        )
                        summary = response.text

                    st.text_area("Summary", summary, height=250)

                except Exception as e:
                    st.error(f"Summary failed: {e}")

            # Delete
            if st.button(f"🗑 Delete {file_name}", key=f"del_{file_name}"):
                shutil.move(file_path, os.path.join(RECYCLE_DIR, file_name))
                st.success("Moved to Recycle Bin.")
                st.experimental_rerun()

            # Rename
            new_base = st.text_input(
                f"Rename {file_name} (without extension)",
                value=os.path.splitext(file_name)[0],
                key=f"rename_input_{file_name}"
            )

            if st.button(f"✏️ Apply Rename for {file_name}", key=f"rename_btn_{file_name}"):
                ext = os.path.splitext(file_name)[1]
                new_name = new_base.strip() + ext
                new_path = os.path.join(VAULT_DIR, new_name)
                if os.path.exists(new_path):
                    st.error("File exists.")
                else:
                    os.rename(file_path, new_path)
                    st.success("Renamed.")
                    st.experimental_rerun()


def page_recycle_bin():
    aaa_header()
    st.subheader("🗑 Recycle Bin")

    files = os.listdir(RECYCLE_DIR)
    if not files:
        st.info("Recycle Bin empty.")
        return

    for f in files:
        file_path = os.path.join(RECYCLE_DIR, f)
        with st.expander(f):

            st.write("Deleted On:", datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).strftime("%Y-%m-%d %H:%M:%S"))

            # PDF preview
            if f.lower().endswith(".pdf"):
                try:
                    pdf = fitz.open(file_path)
                    total = len(pdf)
                    pg = st.number_input(
                        f"Page — {f}",
                        min_value=1,
                        max_value=total,
                        value=1,
                        step=1,
                        key=f"rb_{f}"
                    )
                    page = pdf[pg - 1]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    st.image(pix.tobytes("png"), use_column_width=True)
                    pdf.close()
                except:
                    st.error("Preview failed.")

            elif f.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_path, use_column_width=True)

            if st.button(f"♻ Restore {f}", key=f"restore_{f}"):
                shutil.move(file_path, os.path.join(VAULT_DIR, f))
                st.success("Restored.")
                st.experimental_rerun()

            if st.button(f"❌ Delete Permanently {f}", key=f"perm_{f}"):
                os.remove(file_path)
                st.success("Deleted.")
                st.experimental_rerun()


def page_pdf_preview():
    aaa_header()
    st.subheader("📄 PDF Preview")

    pdfs = [f for f in os.listdir(VAULT_DIR) if f.lower().endswith(".pdf")]
    if not pdfs:
        st.info("No PDFs found.")
        return

    selected = st.selectbox("Select PDF", pdfs)
    path = os.path.join(VAULT_DIR, selected)

    try:
        pdf = fitz.open(path)
        st.write(f"Total pages: {len(pdf)}")

        pg = st.number_input(
            "Page",
            min_value=1, max_value=len(pdf),
            value=1, step=1
        )

        page = pdf[pg - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        st.image(pix.tobytes("png"), use_column_width=True)

    except Exception as e:
        st.error(f"Preview failed: {e}")


def page_ocr():
    aaa_header()
    st.subheader("🔍 Advanced OCR")

    file = st.file_uploader("Upload Image/PDF", type=["png", "jpg", "jpeg", "pdf"])
    if file:
        st.info("Processing…")

        temp_path = os.path.join(PHOTO_DIR, file.name)
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())

        extracted = ""

        # PDF
        if file.name.lower().endswith(".pdf"):
            doc = fitz.open(temp_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img = pix.tobytes("png")
                response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                    ["Extract ALL text.", img]
                )
                extracted += f"\n\n--- PAGE {i+1} ---\n{response.text}"

        # Image
        else:
            img = file.getvalue()
            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                ["Extract ALL text.", img]
            )
            extracted = response.text

        ocr_log = load_json(OCR_DATA_FILE, [])
        ocr_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": file.name,
            "text": extracted
        })
        save_json(OCR_DATA_FILE, ocr_log)

        st.text_area("Extracted Text", extracted, height=300)

    st.write("### Previous OCR Results")
    for entry in load_json(OCR_DATA_FILE, []):
        with st.expander(f"{entry['timestamp']} — {entry['filename']}"):
            st.text(entry["text"])


def page_snapshots():
    aaa_header()
    st.subheader("📸 Data Snapshots")

    if st.button("💾 Create Snapshot"):
        snap = {
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "health_log": load_json(HEALTH_LOG_FILE, []),
            "ocr": load_json(OCR_DATA_FILE, []),
        }

        name = f"snapshot_{snap['timestamp']}.json"
        path = os.path.join(SNAPSHOT_DIR, name)

        with open(path, "w") as f:
            json.dump(snap, f, indent=4)

        st.success(f"Snapshot saved: {name}")
        st.experimental_rerun()

    snaps = sorted(os.listdir(SNAPSHOT_DIR))
    if not snaps:
        st.info("No snapshots.")
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
                    st.success("Restored.")
                    st.experimental_rerun()

            with c2:
                if st.button(f"Delete {snap}", key=f"delete_{snap}"):
                    os.remove(path)
                    st.warning("Deleted.")
                    st.experimental_rerun()


def page_summary():
    aaa_header()
    st.subheader("🧠 AI Summary Report")

    logs = load_json(HEALTH_LOG_FILE, [])
    ocr = load_json(OCR_DATA_FILE, [])

    log_choice = st.selectbox(
        "Select Health Log",
        list(range(len(logs))),
        format_func=lambda i: logs[i]["date"] if logs else "None"
    ) if logs else None

    ocr_choice = st.selectbox(
        "Select OCR Entry",
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

        combined = "\n\n".join(parts)

        model = genai.GenerativeModel("gemini-2.0-flash") 
        response = model.generate_content(
            f"Create a structured medical summary:\n{combined}"
        )

        st.markdown(response.text)


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
        st.info("No data.")
        return

    combined.sort(key=lambda x: x["timestamp"], reverse=True)

    for item in combined:
        with st.expander(f"{item['timestamp']} — {item['type']}"):
            st.write(item["content"])


def page_insights():
    aaa_header()
    st.subheader("🔮 Insights AI")

    st.info("Generates personalised health insights based on ALL data.")

    merged = merge_all_health_data()

    if st.button("✨ Generate AI Insights"):
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content([
                "Analyse full health data and produce structured insights.",
                json.dumps(merged)
            ])
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Failed: {e}")


# ============================================================
# SUMMARY PDF
# ============================================================

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def generate_summary_pdf(merged_data, output_path="summary_report.pdf"):
    try:
        c = canvas.Canvas(output_path, pagesize=letter)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, 10.5 * inch, "AAA – Health Summary Report")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 10.1 * inch, f"Generated: {merged_data.get('generated_at', '')}")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, 9.6 * inch, "1. Health Log Count")
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 9.35 * inch, f"{len(merged_data.get('health_log', []))} entries")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, 8.8 * inch, "2. OCR Extracted")
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 8.55 * inch, f"{len(merged_data.get('ocr_results', []))} files")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, 8.05 * inch, "3. Vault Files")
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 7.8 * inch, f"{len(merged_data.get('vault_files', []))} uploaded")

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1 * inch, 1 * inch,
                     "Crafted by Rajdeep Singh — Artigellence Augmentation Aggregator")
        c.drawString(1 * inch, 0.8 * inch,
                     "Powered by Edge-AI Orchestration Layer • Gemini • Vertex AI")

        c.save()
        return True

    except Exception as e:
        st.error(f"PDF failed: {e}")
        return False


def page_summary_report():
    aaa_header()
    st.subheader("📄 Summary Report (PDF)")

    merged = merge_all_health_data()

    if st.button("📥 Generate Summary PDF"):
        ok = generate_summary_pdf(merged)
        if ok:
            st.success("PDF generated!")
            with open("summary_report.pdf", "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=f,
                    file_name="AAA_Summary_Report.pdf",
                    mime_type="application/pdf"
                )


# ============================================================
# MAIN APP (Footer only once)
# ============================================================

def main():

    st.sidebar.markdown("### 💎 AAA — Health Intelligence")

    pages = {
        "🩺 Health Log": page_health_log,
        "📂 Health Vault": page_vault,
        "📄 PDF Preview": page_pdf_preview,
        "🔍 OCR": page_ocr,
        "🗂 Snapshots": page_snapshots,
        "🤖 Summary AI": page_summary,
        "📊 Merged View": page_merged,
        "📡 Insights AI": page_insights,
        "📁 Vault Manager": page_vault_manager,
        "🗑 Recycle Bin": page_recycle_bin,
        "📘 Summary Report (PDF)": page_summary_report,
    }

    choice = st.sidebar.radio("Navigation", list(pages.keys()))

    pages[choice]()   # load the selected page

    # Always show disclaimer (bottom of page)
    aaa_disclaimer()

    # Footer once
    aaa_footer()


# Entry point
if __name__ == "__main__":
    main()
