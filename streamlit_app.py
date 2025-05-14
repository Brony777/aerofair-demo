from fpdf import FPDF
import streamlit as st
import datetime
import io
import json
import matplotlib.pyplot as plt

# ---------- Autoryzacja ----------
def load_users():
    with open("allowed_users.json") as f:
        return json.load(f)

def check_login(email, password, users):
    for u in users:
        if u["email"] == email and u["password"] == password:
            return u
    return None

if "user" not in st.session_state:
    st.session_state["user"] = None

if not st.session_state["user"]:
    st.title("🔐 Logowanie do aplikacji")
    email = st.text_input("Adres e-mail")
    password = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        users = load_users()
        user = check_login(email, password, users)
        if user:
            st.session_state["user"] = user
            st.success(f"Zalogowano jako {user['name']}")
            st.rerun()
        else:
            st.error("Nieprawidłowy e-mail lub hasło")
    st.stop()

# ---------- Konfiguracja ----------
st.set_page_config(page_title="Mindful Eco Impact AI", page_icon="🌱", layout="wide")
st.title("🌱 Mindful Eco Impact AI")
st.subheader("Monitorowanie i redukcja śladu węglowego Twojej organizacji")
st.markdown("""
Tutaj możesz analizować dane ESG, monitorować emisje CO₂ i generować raporty oraz certyfikaty.
""")

# ---------- Formularz ----------
st.header("📊 Wprowadź dane ESG")

with st.form("esg_form"):
    st.subheader("🔌 Zużycie energii")
    electricity_kwh = st.number_input("Energia elektryczna (kWh)", min_value=0.0)
    heating_kwh = st.number_input("Energia cieplna (kWh)", min_value=0.0)

    st.subheader("🚌 Transport")
    vehicle_km = st.number_input("Samochód firmowy (km)", min_value=0.0)
    flights_hours = st.number_input("Loty służbowe (h)", min_value=0.0)

    st.subheader("📦 Odpady")
    waste_kg = st.number_input("Odpady (kg)", min_value=0.0)

    st.subheader("🧾 Dodatkowe informacje")
    org_name = st.text_input("Nazwa organizacji / produktu")
    cert_date = st.date_input("Data kalkulacji", value=datetime.date.today())
    cert_scope = st.selectbox("Zakres certyfikatu", ["Scope 1+2", "Pełny (1-3)", "Tylko produkcja"])
    comment = st.text_area("Komentarz ESG (opcjonalnie)")
    author = st.text_input("Autor obliczeń")

    submitted = st.form_submit_button("Oblicz ślad węglowy")

# ---------- Obliczenia ----------
if submitted:
    CO2_FACTORS = {
        "electricity": 0.0006,
        "heating": 0.00025,
        "vehicle": 0.00021,
        "flight": 0.09,
        "waste": 0.00045
    }

    co2_total = (
        electricity_kwh * CO2_FACTORS["electricity"] +
        heating_kwh * CO2_FACTORS["heating"] +
        vehicle_km * CO2_FACTORS["vehicle"] +
        flights_hours * CO2_FACTORS["flight"] +
        waste_kg * CO2_FACTORS["waste"]
    )

    esg_data = {
        "Energia elektryczna": electricity_kwh * CO2_FACTORS["electricity"],
        "Energia cieplna": heating_kwh * CO2_FACTORS["heating"],
        "Samochód firmowy": vehicle_km * CO2_FACTORS["vehicle"],
        "Loty służbowe": flights_hours * CO2_FACTORS["flight"],
        "Odpady": waste_kg * CO2_FACTORS["waste"]
    }

    st.success("✅ Obliczono ślad węglowy!")
    st.metric("🌍 Całkowita emisja CO₂e", f"{co2_total:.2f} ton")

    st.subheader("📈 Wykres emisji CO₂e per obszar")
    fig, ax = plt.subplots()
    ax.bar(esg_data.keys(), esg_data.values(), color="skyblue")
    ax.set_title("Emisja CO₂e")
    ax.set_ylabel("tCO₂e")
    plt.xticks(rotation=30)
    st.pyplot(fig)

    # ---------- Raport PDF ----------
    def generate_pdf(data, total_emission, comment, author):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Raport śladu węglowego", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.cell(0, 10, f"Autor: {author}", ln=True)
        pdf.ln(5)

        for k, v in data.items():
            pdf.cell(0, 10, f"{k}: {v:.3f} tCO₂e", ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Całkowita emisja: {total_emission:.3f} ton CO₂e", ln=True)

        if comment:
            pdf.ln(5)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 10, f"Komentarz: {comment}")

        buf = io.BytesIO()
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        buf.write(pdf_bytes)
        buf.seek(0)
        return buf

    # ---------- Certyfikat PDF ----------
    def generate_certificate(org, date_str, total_emission, scope):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 15, "CERTYFIKAT EMISJI CO₂", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "", 13)
        pdf.multi_cell(0, 10,
            f"Potwierdzamy, że organizacja \"{org}\" przeprowadziła kalkulację śladu węglowego "
            f"w dniu {date_str} zgodnie z zakresem: {scope}.\n\n"
            f"Wynik całkowitej emisji wyniósł: {total_emission:.2f} tCO₂e.")

        pdf.ln(20)
        pdf.cell(0, 10, "Wygenerowano przez system Mindful Eco Impact AI (wersja demo)", ln=True)

        buf = io.BytesIO()
        cert_bytes = pdf.output(dest="S").encode("latin1")
        buf.write(cert_bytes)
        buf.seek(0)
        return buf

    # ---------- Przyciski ----------
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Pobierz raport PDF"):
            buf = generate_pdf(esg_data, co2_total, comment, author)
            st.download_button("📥 Pobierz raport", data=buf, file_name="raport_CO2.pdf", mime="application/pdf")

    with col2:
        if st.button("📄 Wygeneruj certyfikat PDF"):
            cert_buf = generate_certificate(org_name, cert_date.strftime("%Y-%m-%d"), co2_total, cert_scope)
            st.download_button("📥 Pobierz certyfikat", data=cert_buf, file_name="certyfikat_CO2.pdf", mime="application/pdf")
