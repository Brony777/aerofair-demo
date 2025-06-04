import streamlit as st
import datetime
import io
import json
import pandas as pd
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
    st.stop()

# ---------- Konfiguracja ----------
st.set_page_config(page_title="QADesk – Audyty ISO", page_icon="✅", layout="wide")
st.title("✅ QADesk – Audyty ISO 9001")
st.caption(f"Zalogowany jako: {st.session_state['user']['name']} ({st.session_state['user']['email']})")

# ---------- Komponenty ----------
components_file = Path("components.json")

def load_components():
    if components_file.exists():
        with open(components_file) as f:
            return json.load(f)
    return []

def save_components(components):
    with open(components_file, "w") as f:
        json.dump(components, f, indent=2)

components = load_components()

st.subheader("🧩 Zarządzanie komponentami")
new_comp = st.text_input("Dodaj nowy komponent")
if st.button("➕ Dodaj komponent") and new_comp:
    if new_comp not in components:
        components.append(new_comp)
        save_components(components)
        st.success(f"Dodano: {new_comp}")
        st.rerun()
    else:
        st.warning("Ten komponent już istnieje.")

if components:
    st.markdown("### ✏️ Edytuj / usuń komponenty")
    selected = st.selectbox("Wybierz komponent do edycji lub usunięcia", components)
    new_name = st.text_input("Zmień nazwę", value=selected)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Zapisz zmiany"):
            idx = components.index(selected)
            components[idx] = new_name
            save_components(components)
            st.success("Zmieniono nazwę komponentu.")
            st.rerun()
    with col2:
        if st.button("🗑️ Usuń komponent"):
            components.remove(selected)
            save_components(components)
            st.success("Usunięto komponent.")
            st.rerun()
else:
    st.info("Brak zdefiniowanych komponentów. Dodaj przynajmniej jeden.")

# ---------- Formularz audytu ----------
st.subheader("📝 Nowy audyt ISO 9001")

if not components:
    st.warning("Przed audytem musisz dodać komponent.")
    st.stop()

selected_component = st.selectbox("📦 Wybierz komponent do audytu", components)

questions = [
    "Czy określono role, obowiązki i uprawnienia związane z jakością w procesach lotniczych?",
    "Czy dostawcy są zatwierdzeni zgodnie z wymaganiami branży lotniczej (np. wg ASL)?",
    "Czy dokumentacja techniczna i zapisy są nadzorowane i zaktualizowane zgodnie z wymaganiami klienta?",
    "Czy przeprowadzono okresowy przegląd zarządzania z uwzględnieniem ryzyk dla bezpieczeństwa lotniczego?",
    "Czy utrzymywana jest identyfikowalność części i materiałów na wszystkich etapach produkcji?",
    "Czy wdrożono działania zapobiegawcze dla niezgodności o krytycznym znaczeniu?",
    "Czy dane z poprzednich audytów i incydentów są wykorzystywane do doskonalenia systemu?",
    "Czy przechowywane są dowody spełnienia wymagań klientów i nadzoru nad zmianami projektowymi?"
]


audit_file = Path("audits.csv")

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
            "component": selected_component,
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
