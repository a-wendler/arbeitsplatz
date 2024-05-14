import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hmac
import json
import os
from sqlalchemy.sql import text

def lade_buchungen(start, ende):
    """Lade Buchungen aus der Datenbank für den gewählten Zeitraum."""
    with conn.session as session:
        daten = session.execute(text('SELECT * FROM buchungen_0_3_0 WHERE datum BETWEEN :start AND :ende;'), params={"start":start,"ende":ende})
        session.commit()
    buchungen = pd.DataFrame(daten, columns=['datum', 'platz', 'name'])
    buchungen['datum'] = pd.to_datetime(buchungen['datum'])
    return buchungen

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Passwort", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Falsches Passwort")
    return False

def speichern_neu(df):
    try:
        for datumsindex, daten in st.session_state['dateneditor']['edited_rows'].items():
            datum = df.iloc[datumsindex].name
            for k,v in daten.items():
                with conn.session as session:
                    if v and len(v) > 0:
                        session.execute(text("INSERT INTO buchungen_0_3_0 (datum, platz, name) VALUES (:datum, :platz, :name) ON DUPLICATE KEY UPDATE name = :name;"), params={"datum": datum,"platz": k,"name": v})
                    else:
                        session.execute(text("DELETE FROM buchungen_0_3_0 WHERE datum = :datum AND platz = :platz;"), params={"datum": datum,"platz": k})
                    session.commit()
    except Exception as e:
        st.session_state.speicherstatus = e
    else:
        st.session_state.speicherstatus = 'Änderungen erfolgreich gespeichert.'

@st.cache_data
def wochenansicht(df: pd.DataFrame, start, ende) -> pd.DataFrame:
    """Erstelle ein leeres Wochen-Dataframe und fülle es mit den vorhandenen Buchungen."""
    # Einlesen der Arbeitsplätze-Konfiguration aus Datei plaetze.json
    with open(f'{verzeichnis_zusatz}plaetze.json', 'r') as f:
        config = json.load(f)
    plaetze = config['plaetze']

    # Erstellen des Datumsindex
    date_index = pd.date_range(start, ende, freq='B')
    
    # Erstellen des leeren Wochen-DataFrames
    aktuelle_woche = pd.DataFrame(columns=plaetze, index=date_index)
    aktuelle_woche.index.names = ['datum']
    aktuelle_woche.columns.names = ['platz']
    
    # die eingelesenen schon gespeicherten buchungen werden mit dem leeren wochen-df kombiniert
    df = df.pivot(index='datum', columns='platz', values='name')
    df.columns.names = ['platz']
    aktuelle_woche = aktuelle_woche.combine_first(df)
    aktuelle_woche = aktuelle_woche[plaetze]
    aktuelle_woche.fillna('', inplace=True)
    return aktuelle_woche

if __name__ == "__main__":
    # anpassung der pfade, jenachdem ob die app im testmodus lokal oder im deplayment bei streamlit läuft
    aktuelles_verzeichnis = os.getcwd()
    if aktuelles_verzeichnis.endswith("/arbeitsplatz/arbeitsplatz"):
        verzeichnis_zusatz = "./"
    else:
        verzeichnis_zusatz = "arbeitsplatz/"

    # Datenbankverbindung herstellen
    conn = st.connection("sql")
    
    # Streamlit App
    
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    if "speicherstatus" not in st.session_state:
        st.session_state.speicherstatus = ""
    
    
    st.title('Arbeitsplatz-Buchungstool 0.3.0')
    st.warning('Neuigkeiten in dieser Version: \n\n1. Automatisches Speichern: beim Verlassen einer Zelle in der Tabelle wird die neu eingetragene Buchung automatisch gespeichert. Ein Speichern-Button ist nicht notwendig. \n\n2. Schnelleres Speichern: die Funktion zum Speichern wurde so überarbeitet, dass Buchungen schneller gespeichert werden.')
    # Kalenderwidget zur Auswahl des Zeitraums
    st.header('1. Datumsbereich wählen')
    col1, col2 = st.columns(2)
    with col1:
        start_datum = st.date_input('Startdatum', datetime.today(), format="DD.MM.YYYY", min_value=datetime.today()-timedelta(days=25), max_value=datetime.today() + timedelta(days=25))
    with col2:
        ende_datum = st.date_input('Enddatum', datetime.today() + timedelta(days=7), format="DD.MM.YYYY", min_value=datetime.today()-timedelta(days=25), max_value=datetime.today() + timedelta(days=25))
    
    if start_datum > ende_datum:
        st.error('Das Startdatum darf nicht nach dem Enddatum liegen!')
    elif start_datum < ende_datum: 
        # Buchungen für den gewählten Zeitraum laden
        buchungen_df = lade_buchungen(start_datum, ende_datum)
        wochen_df = wochenansicht(buchungen_df, start_datum, ende_datum)

        # Dataframe anzeigen und bearbeiten lassen
        st.header('2. Buchungen bearbeiten')
        data_editor = st.data_editor(
            wochen_df, key="dateneditor", column_config={
            "datum": st.column_config.DateColumn(
                "Datum",
                format="ddd, DD.MM.",
            ),
        },
        on_change=speichern_neu,
        args=(wochen_df,)
        )
        speichermeldung = st.container()
        with speichermeldung:
            st.empty()
            if type(st.session_state.speicherstatus) != str:
                st.error("Etwas ist schiefgelaufen. Bitte laden Sie die Seite neu.")
                st.error(st.session_state.speicherstatus)
            elif len(st.session_state.speicherstatus) > 0:
                st.success(st.session_state.speicherstatus)
        
        st.info("Buchungen werden automatisch gespeichert, wenn Sie eine Änderung in einer Zelle vornehmen und in eine andere Zelle oder außerhalb der Tabelle klicken.")
    
  
    st.header('Arbeitsplatzübersicht')
    st.image(f'{verzeichnis_zusatz}grundriss.png', use_column_width=True)

    with st.expander("Datenschutzhinweise"):
        st.write('Die Daten werden auf einem Server beim Hostingdienstleister Hetzner in Nürnberg gespeichert. Es gilt die DSGVO. Zu dem Server hat ausschließlich André Wendler Zugang. Jede Nacht werden automatisch alle Buchungen, die älter als zwei Tage sind, gelöscht. Außerdem werden für jeweils 5 Tage Backups der Datenbank vorgehalten, um Datenverluste zurückspielen zu können. Sie können jederzeit den Inhalt der Datenbank und des Servers bei André Wendler einsehen. Der Code dieser App ist Open Source unter unter www.github.com/a-wendler/arbeitsplatz. Eine Analyse oder weitere Verwendung der Buchungsdaten ist ausgeschlossen. Das Programm selbst läuft beim Dienstleister Streamlit auf amerikanischen Servern. Der Dienstleister erhebt anonymisierte Nutzungsdaten.')