# Streamlit MVP for AeroFAIR Cloud - FAI-as-a-link demo (v2 - ReportLab)
"""
Switched from WeasyPrint -> ReportLab to avoid native Cairo/Pango dependencies
on Streamlit Community Cloud.

Run locally or on Streamlit Cloud:
$ python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
$ pip install streamlit pandas reportlab
$ streamlit run streamlit_app.py

requirements.txt (Cloud):
streamlit==1.34.0
pandas==2.2.2
reportlab==4.1.0
"""

from __future__ import annotations

import io
import tempfile
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle


def parse_cmm_file(uploaded_bytes: bytes, filename: str) -> Optional[pd.DataFrame]:
    """Return DataFrame with (Characteristic, Nominal, Measured, Deviation, Status)."""
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(uploaded_bytes))
        return df

    if filename.lower().endswith(".dfq"):
        text = uploaded_bytes.decode("utf-8", errors="ignore")
        rows = []
        for line in text.splitlines():
            if line.startswith("CC"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    rows.append(
                        {
                            "Characteristic": parts[1],
                            "Nominal": parts[2],
                            "Measured": parts[3],
                            "Deviation": parts[4],
                            "Status": parts[7] if len(parts) > 7 else "?",
                        }
                    )
        if not rows:
            return None
        return pd.DataFrame(rows)

    return None


def build_pdf(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("First Article Inspection Report (Demo)", styles["Title"]))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))

    # Convert dataframe to list of lists
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    elements.append(table)
    elements.append(Paragraph("Demo stamp - electronic signature not applied.", styles["Italic"]))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


st.set_page_config(page_title="AeroFAIR Cloud - FAI Demo", layout="centered")

st.title("AeroFAIR Cloud - FAI Demo (ReportLab)")
st.markdown("Upload plik CSV lub DFQ z CMM, a wygeneruję demo-raport FAI w PDF.")

uploaded_file = st.file_uploader("Wybierz plik pomiarowy", type=["csv", "dfq"])

if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    df = parse_cmm_file(bytes_data, uploaded_file.name)

    if df is None or df.empty:
        st.error("Nie udało się odczytać danych - sprawdź format pliku.")
        st.stop()

    st.subheader("Podgląd pomiarów")
    st.dataframe(df, use_container_width=True)

    if st.button("Generuj FAI PDF"):
        pdf_bytes = build_pdf(df)
        st.success("Raport gotowy!")
        st.download_button(
            label="Pobierz PDF", data=pdf_bytes, file_name="FAI_demo.pdf", mime="application/pdf"
        )
else:
    st.info("Najpierw załaduj plik...")
