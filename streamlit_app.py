import streamlit as st
import datetime
import io
import json
import pandas as pd
from fpdf import FPDF
from pathlib import Path

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
if "audit_df" not in st.session_state:
    st.session_state["audit_df"] = pd.DataFrame()

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

# ---------- Konfiguracja ----------
st.set_page_config(page_title="QADesk – Audyty ISO", page_icon="✅", layout="wide")
st.title("✅ QADesk – Audyty ISO 9001")
st.caption(f"Zalogowany jako: {st.session_state['user']['name']} ({st.session_state['user']['email']})")

questions = [
    "Czy są zdefiniowane role i odpowiedzialności?",
    "Czy istnieje procedura oceny dostawców?",
    "Czy dokumentacja jest aktualna i podpisana?",
    "Czy przeprowadzono przegląd zarządzania?",
    "Czy dostępne są zapisy z poprzednich audytów?"
]

audit_file = Path("audits.csv")

# ---------- Formularz audytu ----------
st.subheader("📝 Nowy audyt")

with st.form("audit_form"):
    auditor = st.text_input("Audytor")
    date = st.date_input("Data audytu", value=datetime.date.today())
    version = st.text_input("Wersja dokumentacji (np. ISO_2023_v2)")
    st.markdown("---")

    results = []
    for i, q in enumerate(questions, start=1):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{i}. {q}**")
        with col2:
            result = st.radio(f"Wynik {i}", ["Tak", "Nie", "N/A"], key=f"q{i}")
            comment = st.text_input(f"Komentarz {i}", key=f"c{i}")
        results.append((q, result, comment))

    submitted = st.form_submit_button("✅ Zakończ audyt i zapisz")

if submitted:
    records = []
    for q, res, com in results:
        records.append({
            "auditor": auditor,
            "date": date.strftime("%Y-%m-%d"),
            "user": st.session_state["user"]["email"],
            "question": q,
            "result": res,
            "comment": com,
            "version": version
        })
    new_df = pd.DataFrame(records)
    if audit_file.exists():
        existing = pd.read_csv(audit_file)
        full_df = pd.concat([existing, new_df], ignore_index=True)
    else:
        full_df = new_df
    full_df.to_csv(audit_file, index=False)
    st.success("✅ Audyt zapisany!")

# ---------- Dashboard ----------
st.subheader("📊 Historia i harmonogram audytów")

if audit_file.exists():
    df = pd.read_csv(audit_file)
    st.dataframe(df)
    st.download_button("📥 Eksportuj do CSV", df.to_csv(index=False).encode("utf-8"), "audits_export.csv")

    st.markdown("### ✏️ Edytuj istniejący wpis")
    selected_row = st.number_input("Nr rekordu do edycji (0 = pierwszy)", min_value=0, max_value=len(df)-1, step=1)
    if st.button("Zastosuj zmianę (ustaw wynik 'Tak')"):
        df.at[selected_row, "result"] = "Tak"
        df.to_csv(audit_file, index=False)
        st.success("Wynik zaktualizowany!")
else:
    st.info("Brak danych audytowych.")
