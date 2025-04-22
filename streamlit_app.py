# Streamlit MVP for AeroFAIR Cloud – FAI‑as‑a‑link demo
"""
Quick demo that:
1. Uploads CMM result file (CSV or Zeiss DFQ – super‑simplified parser).
2. Displays the measurements in a dataframe.
3. Builds a PDF First‑Article‑Inspection report using WeasyPrint.
4. Offers direct download & data‑URI link.

Run locally:
$ python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
$ pip install streamlit pandas weasyprint
$ streamlit run streamlit_app.py

Or push to Streamlit Community Cloud → it auto‑installs requirements.
"""

from __future__ import annotations

import base64
import io
import tempfile
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from weasyprint import HTML


def parse_cmm_file(uploaded_bytes: bytes, filename: str) -> Optional[pd.DataFrame]:
    """Return DataFrame with (Characteristic, Nominal, Measured, Deviation, Status)."""
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(uploaded_bytes))
        return df

    if filename.lower().endswith(".dfq"):
        # Minimalistic DFQ parser (Zeiss Calypso) – demo only
        text = uploaded_bytes.decode("utf-8", errors="ignore")
        rows = []
        for line in text.splitlines():
            if line.startswith("CC"):
                parts = [p.strip() for p in line.split(",")]
                # Zeiss DFQ CC‑line: CC,<id>,<nominal>,<measured>,<dev> ,<plus_tol>,<minus_tol>,<status>
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


st.set_page_config(page_title="AeroFAIR Cloud – FAI Demo", page_icon="🛠️", layout="centered")

st.title("🛠️ AeroFAIR Cloud – FAI Demo")
st.markdown("Upload plik CSV lub DFQ z CMM, a wygeneruję demo‑raport FAI w PDF.")

uploaded_file = st.file_uploader("Wybierz plik pomiarowy", type=["csv", "dfq"])  # noqa: E501

if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    df = parse_cmm_file(bytes_data, uploaded_file.name)

    if df is None or df.empty:
        st.error("Nie udało się odczytać danych – sprawdź format pliku.")
        st.stop()

    st.subheader("Podgląd pomiarów")
    st.dataframe(df, use_container_width=True)

    if st.button("Generuj FAI PDF"):
        # Build simple HTML
        html = f"""
        <h1>First Article Inspection Report (Demo)</h1>
        <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} – DEMO</p>
        {df.to_html(index=False)}
        <p style='color:red;'>Demo stamp – electronic signature not applied.</p>
        """

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            HTML(string=html).write_pdf(tmp_file.name)
            tmp_file.seek(0)
            pdf_bytes = tmp_file.read()

        st.success("Raport gotowy!")
        st.download_button(
            label="📄 Pobierz PDF", data=pdf_bytes, file_name="FAI_demo.pdf", mime="application/pdf"
        )

        # Build data‑URI link to open in new tab
        b64 = base64.b64encode(pdf_bytes).decode()
        data_uri = f"data:application/pdf;base64,{b64}"
        st.markdown(f"[Otwórz w nowej karcie]({data_uri})", unsafe_allow_html=True)

else:
    st.info("Najpierw załaduj plik…")
