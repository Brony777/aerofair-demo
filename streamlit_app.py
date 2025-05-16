import streamlit as st
import datetime
import io
import json
from fpdf import FPDF

# ---------- Autoryzacja ----------
def load_users():
    with open("users.json") as f:
        return json.load(f)

def check_login(email, password, users):
    for u in users:
        if u["email"] == email and u["password"] == password:
            return u
    return None

if "user" not in st.session_state:
    st.session_state["user"] = None

if not st.session_state["user"]:
    st.title("🔐 Logowanie do QADesk")
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

# ---------- Aplikacja główna ----------
st.set_page_config(page_title="QADesk – Audyty ISO", page_icon="✅", layout="wide")
st.title("✅ QADesk – Audyty ISO 9001")
st.caption(f"Zalogowany jako: {st.session_state['user']['name']} ({st.session_state['user']['email']})")

st.subheader("📋 Formularz audytu ISO 9001")

questions = [
    "Czy są zdefiniowane role i odpowiedzialności?",
    "Czy istnieje procedura oceny dostawców?",
    "Czy dokumentacja jest aktualna i podpisana?",
    "Czy przeprowadzono przegląd zarządzania?",
    "Czy dostępne są zapisy z poprzednich audytów?"
]

results = []
with st.form("audit_form"):
    auditor = st.text_input("Imię i nazwisko audytora")
    date = st.date_input("Data audytu", value=datetime.date.today())

    st.markdown("---")
    for i, q in enumerate(questions, start=1):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{i}. {q}**")
        with col2:
            result = st.radio(f"Wynik {i}", ["Tak", "Nie", "N/A"], key=f"q{i}")
            comment = st.text_input(f"Komentarz {i}", key=f"c{i}")
        results.append((q, result, comment))
    submitted = st.form_submit_button("✅ Zakończ audyt i generuj PDF")

if submitted:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Raport audytu jakości – ISO 9001", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Audytor: {auditor}", ln=True)
    pdf.cell(0, 10, f"Data: {date.strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(0, 10, f"Użytkownik: {st.session_state['user']['email']}", ln=True)
    pdf.ln(5)

    for i, (q, res, com) in enumerate(results, start=1):
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 8, f"{i}. {q}")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Wynik: {res}", ln=True)
        if com:
            pdf.multi_cell(0, 8, f"Komentarz: {com}")
        pdf.ln(2)

    pdf.ln(10)
    pdf.cell(0, 10, "Wygenerowano przez QADesk", ln=True)

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    pdf_buffer = io.BytesIO(pdf_bytes)
    st.download_button("📥 Pobierz raport PDF", data=pdf_buffer, file_name="raport_audytu.pdf", mime="application/pdf")
