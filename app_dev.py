# AAA Health – Premium Rewrite (Concise Functional Version)
# NOTE: This is a stable, safe, simplified premium version maintaining all key features.

import streamlit as st
import os
from datetime import datetime
import json
from pathlib import Path
import shutil
import pandas as pd
import google.generativeai as genai

BASE = Path(__file__).parent
VAULT = BASE / "vault"
SNAP = BASE / "snapshots"
RECYCLE = BASE / "recycle_bin"
for d in [VAULT, SNAP, RECYCLE]:
    d.mkdir(exist_ok=True)

DATA = BASE / "aaa_data.json"

def load_data():
    if not DATA.exists():
        return {"logs": [], "last_update": None}
    try:
        return json.load(open(DATA, "r"))
    except:
        return {"logs": [], "last_update": None}

def save_data(d):
    json.dump(d, open(DATA, "w"), indent=4)

app = load_data()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

st.set_page_config(page_title="AAA Health", layout="wide")

def header():
    st.markdown("## ARTIGELLENCE — AAA HEALTH")
    st.caption("Personal Health Intelligence • Edge-AI Augmentation Layer")

def footer():
    st.markdown("---")
    st.caption("© 2025 Artigellence • This is not medical advice.")

def page_dashboard():
    header()
    st.subheader("📊 Health Dashboard")

    if app.get("last_update"):
        st.success(f"Last Update: {app['last_update']}")
    else:
        st.info("No health updates yet.")

    st.write("### Recent Logs")
    if not app["logs"]:
        st.info("No logs yet.")
    else:
        for i, log in enumerate(reversed(app["logs"][-5:])):
            with st.expander(f"Log {len(app['logs']) - i}"):
                st.write(log)

    footer()

def page_summary():
    header()
    st.subheader("🤖 AI Health Summary")

    up = st.file_uploader("Upload any health document", type=["pdf","jpg","jpeg","png"])
    if up:
        p = VAULT / up.name
        open(p, "wb").write(up.read())
        st.success("File saved to Vault.")

        with st.spinner("Analyzing with Gemini..."):
            try:
                m = genai.GenerativeModel("gemini-2.0-flash")
                out = m.generate_content("Summarize the health insights from this file.")
                st.write(out.text)
                app["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(app)
            except Exception as e:
                st.error(str(e))
    footer()

def page_insights():
    header()
    st.subheader("💡 Insights")
    logs = app["logs"]
    if not logs:
        st.info("Add logs to generate insights.")
        footer()
        return
    text = " ".join(logs).lower()
    if "sleep" in text:
        st.success("Sleep patterns detected — track your hours.")
    if "bp" in text or "blood pressure" in text:
        st.success("Blood pressure mentioned — monitor regularly.")
    if "glucose" in text:
        st.success("Glucose readings detected — compare fasting vs post‑meal.")
    footer()

def page_vault():
    header()
    st.subheader("📁 Vault")
    files = os.listdir(VAULT)
    if not files:
        st.info("Vault empty.")
        footer()
        return

    for f in files:
        p = VAULT / f
        with st.expander(f):
            if st.button(f"Delete {f}", key=f"del_{f}"):
                shutil.move(p, RECYCLE / f)
                st.warning("Moved to Recycle Bin.")
                st.experimental_rerun()
    footer()

def page_pdf_preview():
    header()
    st.subheader("🧾 PDF Preview")
    pdfs = [f for f in os.listdir(VAULT) if f.lower().endswith(".pdf")]
    if not pdfs:
        st.info("No PDFs.")
        footer()
        return
    for f in pdfs:
        p = VAULT / f
        with st.expander(f):
            st.download_button("Download", open(p,"rb"), file_name=f)
    footer()

def page_snapshots():
    header()
    st.subheader("📸 Snapshots")
    if st.button("Create Snapshot"):
        name = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        shutil.make_archive(str(SNAP/name).replace(".zip",""), "zip", VAULT)
        st.success("Snapshot created.")
    for f in os.listdir(SNAP):
        p = SNAP / f
        st.download_button(f"Download {f}", open(p,"rb"), file_name=f)
    footer()

def page_recycle():
    header()
    st.subheader("🗑️ Recycle Bin")
    files = os.listdir(RECYCLE)
    if not files:
        st.info("Recycle Bin empty.")
        footer()
        return
    for f in files:
        p = RECYCLE / f
        with st.expander(f):
            if st.button(f"Restore {f}", key=f"r_{f}"):
                shutil.move(p, VAULT / f)
                st.success("Restored.")
                st.experimental_rerun()
            if st.button(f"Delete Permanently {f}", key=f"d_{f}"):
                os.remove(p)
                st.error("Deleted permanently.")
                st.experimental_rerun()
    footer()

def page_regional():
    header()
    st.subheader("🌍 Regional Wellness Snapshot")
    st.metric("Avg NSW Steps", "6,300")
    st.metric("Avg NSW Sleep", "6.7 hrs")
    footer()

def page_close_circle():
    header()
    st.subheader("🛡️ Close Circle")
    st.info("Future feature: share limited health reports securely with trusted family.")
    footer()

def page_trend():
    header()
    st.subheader("📈 Health Score Trend (Demo)")
    df = pd.DataFrame({"Day": range(1,11), "Score":[80,82,79,81,85,83,84,86,87,88]})
    st.line_chart(df)
    footer()

PAGES = {
    "Dashboard": page_dashboard,
    "AI Summary": page_summary,
    "Insights": page_insights,
    "Vault": page_vault,
    "PDF Preview": page_pdf_preview,
    "Snapshots": page_snapshots,
    "Recycle Bin": page_recycle,
    "Regional Insights": page_regional,
    "Close Circle": page_close_circle,
    "Health Score Trend": page_trend,
}

choice = st.sidebar.radio("Navigation", list(PAGES.keys()))
PAGES[choice]()
