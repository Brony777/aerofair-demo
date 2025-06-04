import streamlit as st
import datetime
import io
import json
import pandas as pd
from pathlib import Path
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
    st.set_page_config(page_title="QADesk – Logowanie", layout="centered")
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

    st.markdown("""
    ---
    ❓ Nie masz konta?  
    👉  Wyślij wiadomość, aby otrzymać dane logowania.  
    ✉️ Tytuł e-maila: **QADEMO**
    """)
    st.stop()

# ---------- Konfiguracja ----------
st.set_page_config(page_title="QADesk – Audyty ISO", page_icon="✅", layout="wide")
st.title("✅ QADesk – Audyty ISO 9001")
st.caption(f"Zalogowany jako: {st.session_state['user']['name']} ({st.session_state['user']['email']})")

component_file = Path("components.json")
audit_file = Path("audits.csv")

# ---------- Nawigacja ----------
menu = st.sidebar.radio("📁 Wybierz widok", ["➕ Nowy audyt", "🧩 Zarządzanie komponentami", "📂 Historia audytów"])

# ---------- Komponenty ----------
def load_components():
    if component_file.exists():
        return json.loads(component_file.read_text())
    return []

def save_components(components):
    component_file.write_text(json.dumps(components, indent=2, ensure_ascii=False))

components = load_components()

# ---------- Widok: Dodawanie audytu ----------
if menu == "➕ Nowy audyt":
    st.subheader("📝 Nowy audyt ISO 9001")

    if not components:
        st.warning("⚠️ Najpierw dodaj przynajmniej jeden komponent w menu „Zarządzanie komponentami”.")
        st.stop()

    with st.form("audit_form"):
        component = st.selectbox("Komponent audytowany", components)
        auditor = st.text_input("Audytor")
        date = st.date_input("Data audytu", value=datetime.date.today())
        version = st.text_input("Wersja dokumentacji (np. ISO_2023_v2)")
        st.markdown("---")

        questions = [
            "Czy zdefiniowano i udokumentowano role oraz odpowiedzialności dla komponentu?",
            "Czy komponent przeszedł zatwierdzoną procedurę oceny jakości dostawcy?",
            "Czy dokumentacja komponentu jest aktualna i została zatwierdzona?",
            "Czy komponent podlegał przeglądowi technicznemu/zarządczemu?",
            "Czy przechowywane są archiwalne wyniki wcześniejszych audytów komponentu?"
        ]

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
                "component": component,
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

# ---------- Widok: Zarządzanie komponentami ----------
elif menu == "🧩 Zarządzanie komponentami":
    st.subheader("🧩 Lista komponentów")
    if components:
        st.write("Obecne komponenty:")
        st.write(components)

    with st.form("add_component"):
        new_comp = st.text_input("Dodaj nowy komponent")
        if st.form_submit_button("➕ Dodaj"):
            if new_comp and new_comp not in components:
                components.append(new_comp)
                save_components(components)
                st.success(f"✅ Dodano: {new_comp}")
            else:
                st.warning("⚠️ Komponent już istnieje lub jest pusty.")

    st.markdown("---")
    with st.form("delete_component"):
        to_delete = st.selectbox("Usuń komponent", components)
        if st.form_submit_button("🗑 Usuń"):
            components.remove(to_delete)
            save_components(components)
            st.success(f"❌ Usunięto: {to_delete}")

# ---------- Widok: Historia audytów ----------
elif menu == "📂 Historia audytów":
    st.subheader("📂 Przegląd zapisanych audytów")

    if audit_file.exists():
        df = pd.read_csv(audit_file)
        if not df.empty:
            selected_component = st.selectbox("Filtruj po komponencie", options=["-- wszystkie --"] + sorted(df["component"].unique()))
            if selected_component != "-- wszystkie --":
                df = df[df["component"] == selected_component]

            st.dataframe(df, use_container_width=True)
            st.markdown(f"Wyświetlono **{len(df)}** wpisów.")
            st.download_button("📥 Eksportuj jako CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="audits_export.csv", mime="text/csv")
        else:
            st.info("Brak danych audytowych.")
    else:
        st.info("Nie znaleziono pliku `audits.csv`.")
