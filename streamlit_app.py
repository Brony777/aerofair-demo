# Streamlit MVP – Carbon Footprint Calculator (AeroGreen Demo) + PDF + Upload + Komentarz
"""
Rozszerzona wersja demo aplikacji SaaS liczącej ślad węglowy:
- PDF raport z FPDF
- Możliwość uploadu pliku Excela z danymi wejściowymi
- Pole komentarza ESG + autor
"""

import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime

st.set_page_config(page_title="Carbon Footprint Calculator", layout="centered")
st.title("🌍 AeroGreen – Kalkulator śladu węglowego komponentu")
st.markdown("Wprowadź dane lub załaduj plik Excela, aby obliczyć emisję CO₂ (kg/szt.)")

# PDF generator
class CO2PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Raport emisji CO₂ – AeroGreen", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Wygenerowano: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC", 0, 0, "C")

    def add_result(self, data, total, komentarz, autor):
        self.set_font("Arial", "", 12)
        for k, v in data.items():
            self.cell(0, 10, f"{k}: {v:.2f} kg CO₂", ln=True)
        self.ln(5)
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, f"Całkowita emisja: {total:.2f} kg CO₂/szt.", ln=True)
        if komentarz:
            self.set_font("Arial", "", 11)
            self.multi_cell(0, 10, f"\nKomentarz: {komentarz}")
        if autor:
            self.set_font("Arial", "I", 10)
            self.cell(0, 10, f"Obliczenia wykonał: {autor}", ln=True)

# Upload lub ręczne dane
uploaded = st.file_uploader("Lub załaduj plik Excela z danymi procesu", type="xlsx")

if uploaded:
    df = pd.read_excel(uploaded)
    st.write("📋 Załadowane dane:", df)
    row = df.iloc[0]
    energy_kwh = row.get("energia_kWh", 0.0)
    material_type = row.get("material", "Stal")
    material_kg = row.get("material_kg", 0.0)
    diesel_liters = row.get("diesel_l", 0.0)
    transport_km = row.get("transport_km", 0.0)
    transport_tons = row.get("transport_t", 0.0)
else:
    energy_kwh = st.number_input("Zużycie energii elektrycznej [kWh]", min_value=0.0, step=0.1)
    material_type = st.selectbox("Materiał główny", ["Stal", "Aluminium"])
    material_kg = st.number_input("Zużycie materiału [kg]", min_value=0.0, step=0.1)
    diesel_liters = st.number_input("Zużycie paliwa (olej napędowy) [l]", min_value=0.0, step=0.1)
    transport_km = st.number_input("Transport do klienta [km]", min_value=0.0, step=1.0)
    transport_tons = st.number_input("Masa transportowana [t]", min_value=0.0, step=0.1)

komentarz = st.text_area("Komentarz do obliczeń (opcjonalny)")
autor = st.text_input("Autor obliczeń (opcjonalnie)")

if st.button("Oblicz ślad węglowy"):
    EF = {
        "power": 0.65,
        "steel": 2.1,
        "alu": 10.0,
        "diesel": 2.67,
        "truck": 0.12
    }
    em_power = energy_kwh * EF["power"]
    em_material = material_kg * (EF["steel"] if material_type == "Stal" else EF["alu"])
    em_fuel = diesel_liters * EF["diesel"]
    em_transport = transport_km * transport_tons * EF["truck"]

    total = em_power + em_material + em_fuel + em_transport
    parts = {
        "Energia": em_power,
        f"Materiał ({material_type})": em_material,
        "Paliwo": em_fuel,
        "Transport": em_transport
    }

    st.success(f"Całkowita emisja CO₂: {total:.2f} kg / sztuka")
    st.json(parts)

    if st.button("📄 Wygeneruj raport PDF"):
        pdf = CO2PDF()
        pdf.add_page()
        pdf.add_result(parts, total, komentarz, autor)
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        st.download_button(
            label="📥 Pobierz raport CO₂ (PDF)",
            data=pdf_buffer,
            file_name="raport_sladu_weglowego.pdf",
            mime="application/pdf"
        )
else:
    st.info("Wprowadź dane lub załaduj plik, aby rozpocząć obliczenia.")
