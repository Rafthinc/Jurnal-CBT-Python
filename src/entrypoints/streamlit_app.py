import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from src.domain.models import CBTEntry
from src.services.pdf_service import PDFGeneratorService
from src.services.database_service import DatabaseService

# Initialize database service
db_service = DatabaseService()

# --- Data for examples ---
EMOTIONS_LIST = [
    "Anxietate", "Tristețe", "Furie", "Gelozie", 
    "Invidie", "Dezgust", "Bucurie", "Iubire"
]

SITUATIONS_EXAMPLES = [
    "Alege un exemplu...",
    "Șeful mi-a făcut o observație.",
    "Partenerul a întârziat fără să mă anunțe.",
    "Am primit o factură neașteptată.",
    "Trebuie să vorbesc în fața unui public.",
    "Un prieten a anulat întâlnirea în ultimul moment."
]

THOUGHTS_BY_EMOTION = {
    "Anxietate": ["Ceva groaznic se va întâmpla.", "Nu voi face față situației.", "Voi face o greșeală și voi fi judecat.", "O să mă fac de râs."],
    "Tristețe": ["Nu sunt bun de nimic.", "Nimic nu are sens.", "Situația nu se va îmbunătăți niciodată.", "Sunt complet singur."],
    "Furie": ["Nu este corect să fiu tratat așa!", "Nu ar trebui să se comporte așa cu mine!", "Este o lipsă totală de respect.", "M-a făcut intenționat să sufăr."],
    "Gelozie": ["O să mă părăsească pentru altcineva.", "Îi pasă mai mult de altcineva decât de mine.", "Nu sunt suficient de bun pentru el/ea."],
    "Invidie": ["El/ea are totul și eu nu am nimic.", "Nu merită succesul pe care îl are.", "De ce ei au noroc și eu nu?"],
    "Dezgust": ["Asta este absolut dezgustător.", "Nu pot suporta să fiu în preajma acestui lucru/acestei persoane."],
    "Bucurie": ["Lucrurile merg exact așa cum mi-am dorit.", "Sunt norocos și recunoscător pentru ce am.", "Am reușit!"],
    "Iubire": ["Sunt apreciat și iubit.", "Vreau să îi ofer tot ce e mai bun acestei persoane."]
}

BEHAVIORS_BY_EMOTION = {
    "Anxietate": ["Am evitat situația.", "Am cerut reasigurări de la ceilalți.", "M-am agitat și am încercat să controlez totul."],
    "Tristețe": ["M-am izolat în cameră.", "Am plâns.", "Am stat în pat toată ziua fără să fac nimic."],
    "Furie": ["Am ridicat vocea.", "M-am certat cu persoana respectivă.", "Am plecat trântind ușa."],
    "Gelozie": ["I-am verificat telefonul/mesajele.", "I-am cerut explicații detaliate.", "M-am purtat rece și distant."],
    "Invidie": ["Am criticat persoana respectivă față de alții.", "M-am retras și am evitat persoana.", "Am încercat să îi minimizez succesul."],
    "Dezgust": ["M-am îndepărtat imediat.", "Am făcut o grimasă și am refuzat interacțiunea."],
    "Bucurie": ["Am sărbătorit cu cei dragi.", "Am zâmbit și am fost plin de energie.", "Am fost generos cu ceilalți."],
    "Iubire": ["I-am făcut o surpriză.", "I-am spus cât de mult înseamnă pentru mine.", "I-am oferit sprijin necondiționat."]
}

def init_session_state():
    if "situatie_text" not in st.session_state:
        st.session_state.situatie_text = ""
    if "ganduri_text" not in st.session_state:
        st.session_state.ganduri_text = ""
    if "comportament_text" not in st.session_state:
        st.session_state.comportament_text = ""

def apply_situatie():
    val = st.session_state.situatie_select
    if val and val not in ["Alege un exemplu...", "Selectează cel puțin o emoție pentru exemple specifice."]:
        if st.session_state.situatie_text:
            st.session_state.situatie_text += "\n" + val
        else:
            st.session_state.situatie_text = val
        st.session_state.situatie_select = "Alege un exemplu..."

def apply_gand():
    val = st.session_state.gand_select
    if val and val not in ["Alege un exemplu...", "Selectează cel puțin o emoție pentru exemple specifice."]:
        if st.session_state.ganduri_text:
            st.session_state.ganduri_text += "\n" + val
        else:
            st.session_state.ganduri_text = val
        st.session_state.gand_select = "Alege un exemplu..."

def apply_comportament():
    val = st.session_state.comportament_select
    if val and val not in ["Alege un exemplu...", "Selectează cel puțin o emoție pentru exemple specifice."]:
        if st.session_state.comportament_text:
            st.session_state.comportament_text += "\n" + val
        else:
            st.session_state.comportament_text = val
        st.session_state.comportament_select = "Alege un exemplu..."

def clear_form():
    st.session_state.situatie_text = ""
    st.session_state.ganduri_text = ""
    st.session_state.comportament_text = ""
    st.session_state.emotii_multiselect = []
    st.session_state.intensitate_slider = 5
    st.session_state.veridicitate_slider = 5
    st.session_state.situatie_select = "Alege un exemplu..."
    # The others dynamically depend on emotions, but we can set them safely:
    if "gand_select" in st.session_state:
        st.session_state.gand_select = "Alege un exemplu..."
    if "comportament_select" in st.session_state:
        st.session_state.comportament_select = "Alege un exemplu..."

def show_cbt_form(username: str):
    st.info("Completează câmpurile de mai jos pentru a genera fișa de conceptualizare. Este mai natural să începi cu emoția resimțită.")
    
    # --- 1. Emoții ---
    st.header("1. Ce ai simțit? (Emoția)")
    emotii_alese = st.multiselect("Selectează emoțiile resimțite:", EMOTIONS_LIST, key="emotii_multiselect")
    intensitate_emotie = st.slider("Intensitatea emoțională (0 - minim, 10 - maxim)", 0, 10, 5, key="intensitate_slider")

    # --- 2. Situație ---
    st.header("2. Ce s-a întâmplat? (Situația)")
    st.selectbox("Exemple de situații:", SITUATIONS_EXAMPLES, key="situatie_select", on_change=apply_situatie)
    situatie = st.text_area("Descrie situația ta (sau folosește un exemplu de mai sus):", key="situatie_text")

    # --- 3. Gânduri ---
    st.header("3. Ce gândeai în acel moment? (Gânduri)")
    
    ganduri_examples = ["Alege un exemplu..."]
    if emotii_alese:
        for emotie in emotii_alese:
            if emotie in THOUGHTS_BY_EMOTION:
                ganduri_examples.extend(THOUGHTS_BY_EMOTION[emotie])
    else:
        ganduri_examples.append("Selectează cel puțin o emoție pentru exemple specifice.")
        
    st.selectbox("Exemple de gânduri (specifice emoțiilor alese):", ganduri_examples, key="gand_select", on_change=apply_gand)
    ganduri = st.text_area("Notează gândurile tale (sau alege din exemple):", key="ganduri_text")
    veridicitate_ganduri = st.slider("Cât de adevărate crezi că sunt aceste gânduri? (0 - deloc, 10 - complet)", 0, 10, 5, key="veridicitate_slider")

    # --- 4. Comportament ---
    st.header("4. Ce ai făcut? (Comportamentul)")
    
    comportamente_examples = ["Alege un exemplu..."]
    if emotii_alese:
        for emotie in emotii_alese:
            if emotie in BEHAVIORS_BY_EMOTION:
                comportamente_examples.extend(BEHAVIORS_BY_EMOTION[emotie])
    else:
        comportamente_examples.append("Selectează cel puțin o emoție pentru exemple specifice.")
        
    st.selectbox("Exemple de comportamente:", comportamente_examples, key="comportament_select", on_change=apply_comportament)
    comportament = st.text_area("Ce ai făcut ca reacție? (sau alege din exemple):", key="comportament_text")

    st.markdown("---")
    # --- Generare Raport ---
    col1, col2 = st.columns([1, 1])
    with col1:
        submit_btn = st.button("Generează Raport și Salvează", type="primary")
    with col2:
        st.button("🔄 Resetează Formularul", on_click=clear_form)

    if submit_btn:
        if all([emotii_alese, situatie, ganduri, comportament]):
            entry = CBTEntry(
                situatie=situatie, 
                ganduri=ganduri, 
                veridicitate_ganduri=veridicitate_ganduri,
                emotii=emotii_alese, 
                intensitate_emotie=intensitate_emotie,
                comportament=comportament
            )
            
            # Save to Database
            db_service.add_cbt_entry(username, entry)
            st.success("Înregistrarea a fost salvată cu succes în istoricul tău!")
            
            # Fetch history for chart
            history = db_service.get_user_entries(username)
            
            # Generate PDF with chart
            pdf_bytes = PDFGeneratorService.create_cbt_report(entry, history)
            
            st.download_button(
                label="📥 Descarcă PDF", 
                data=pdf_bytes, 
                file_name="cbt_report.pdf", 
                mime="application/pdf"
            )
            
            st.info("Formularul poate fi golit acum apăsând butonul de 'Resetează Formularul' de mai sus.")
        else:
            st.warning("Te rugăm să completezi toate câmpurile obligatorii (situație, gânduri, emoții, comportament).")


def show_dashboard(username: str):
    st.header("📊 Evoluția Ta Emoțională")
    history = db_service.get_user_entries(username)
    
    if not history:
        st.info("Încă nu ai nicio înregistrare CBT. Completează un jurnal nou pentru a vedea graficul!")
        return

    # Data prep for charting
    df = pd.DataFrame([
        {
            "Data": entry.data_creare, 
            "Intensitate Emoție": entry.intensitate_emotie,
            "Emoții": ", ".join(entry.emotii),
            "Situație": entry.situatie
        } for entry in history
    ])
    df['Data'] = pd.to_datetime(df['Data'], format="%d/%m/%Y %H:%M:%S")
    df = df.set_index('Data')
    
    st.line_chart(df[['Intensitate Emoție']])
    
    st.subheader("Istoric Jurnale")
    st.dataframe(df.reset_index()[['Data', 'Intensitate Emoție', 'Emoții', 'Situație']], use_container_width=True)

def show_admin_dashboard():
    st.header("👑 Panou de Administrare")
    total_users, total_entries, users_data = db_service.get_admin_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Utilizatori Înregistrați", total_users)
    col2.metric("Total Jurnale CBT Generate", total_entries)
    
    st.subheader("Lista Utilizatorilor")
    if users_data:
        df_users = pd.DataFrame(users_data, columns=["Username (Email)", "Email", "Nume Complet"])
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("Niciun utilizator înregistrat momentan.")

def run_ui():
    st.set_page_config(page_title="CBT Log - apps4mind", layout="centered")
    init_session_state()

    credentials = db_service.load_users_for_auth()

    authenticator = stauth.Authenticate(
        credentials,
        'cbt_cookie',
        'cbt_signature_key',
        cookie_expiry_days=30
    )

    st.title("🧠 Jurnal CBT & Evoluție")

    # Login Logic
    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    if st.session_state.get("authentication_status"):
        username = st.session_state["username"]
        with st.sidebar:
            st.write(f'Bun venit, *{st.session_state["name"]}*!')
            authenticator.logout('Logout', 'main')

        # --- ADMIN CONFIGURATION ---
        # Modify this list to include your actual email address
        ADMIN_EMAILS = ["admin@apps4mind.ro"] 
        is_admin = username in ADMIN_EMAILS

        if is_admin:
            tab1, tab2, tab3 = st.tabs(["📝 Jurnal Nou", "📈 Evoluție și Istoric", "👑 Admin"])
            with tab1:
                show_cbt_form(username)
            with tab2:
                show_dashboard(username)
            with tab3:
                show_admin_dashboard()
        else:
            tab1, tab2 = st.tabs(["📝 Jurnal Nou", "📈 Evoluție și Istoric"])
            with tab1:
                show_cbt_form(username)
            with tab2:
                show_dashboard(username)

    elif st.session_state.get("authentication_status") is False:
        st.error('Username sau parolă incorectă')
    elif st.session_state.get("authentication_status") is None:
        st.warning('Te rugăm să te conectezi pentru a accesa și salva jurnalele tale.')
        
        # Registration logic
        with st.expander("Nu ai cont? Înregistrează-te rapid aici"):
            with st.form("register_form"):
                st.markdown("### Înregistrare Simplificată")
                new_email = st.text_input("Email (va fi folosit ca Username)")
                new_name = st.text_input("Nume complet")
                submit_register = st.form_submit_button("Creează cont automat")
                
                if submit_register:
                    if new_name and new_email:
                        if new_email in credentials.get('usernames', {}):
                            st.error("Există deja un cont cu acest email.")
                        else:
                            import secrets
                            import string
                            import bcrypt
                            
                            # Generate an 8-character random password
                            chars = string.ascii_letters + string.digits
                            generated_pwd = ''.join(secrets.choice(chars) for _ in range(8))
                            
                            # Hash password for streamlit-authenticator compatibility
                            hashed_pwd = bcrypt.hashpw(generated_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            
                            # Save to DB (email is used as username)
                            db_service.save_user(new_email, new_email, new_name, hashed_pwd)
                            
                            st.success("Cont creat cu succes!")
                            st.info(f"**Username / Email:** {new_email}\n\n**Parola ta generată:** `{generated_pwd}`\n\n*(Copiază această parolă într-un loc sigur! Te poți loga imediat cu ea în formularul de mai sus.)*")
                    else:
                        st.warning("Te rugăm să completezi numele și email-ul.")

if __name__ == "__main__":
    run_ui()