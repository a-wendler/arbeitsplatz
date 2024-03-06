import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import hmac
import json
import os

def lade_buchungen(start, ende):
    """Lade Buchungen aus der Datenbank für den gewählten Zeitraum."""
    c.execute('SELECT * FROM buchungen WHERE datum BETWEEN ? AND ?', (start, ende))
    buchungen = pd.DataFrame(c.fetchall(), columns=['datum', 'platz', 'name'])
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

# Hilfsfunktion zum Speichern der Buchungen in der Datenbank
def speichere_buchungen(df):
    """Speichere Buchungen in der Datenbank."""
    
    c.execute('DELETE FROM buchungen WHERE datum BETWEEN ? AND ?', (df.index.min().strftime('%Y-%m-%d'), df.index.max().strftime('%Y-%m-%d')))
    for datum, row in df.iterrows():
        for platz, name in enumerate(row, start=1):
            if pd.notnull(name):
                c.execute('INSERT INTO buchungen (datum, platz, name) VALUES (?, ?, ?)', (datum.date().strftime('%Y-%m-%d'), platz, name))
    conn.commit()

# Beispieldaten hinzufügen, wenn die Tabelle leer ist
def fuege_beispieldaten_hinzu():
    """Füge Beispieldaten hinzu, wenn die Tabelle leer ist."""
    heute = datetime.today().date()
    c.execute('SELECT * FROM buchungen WHERE datum = ?', (heute,))
    if not c.fetchall():
        c.execute('INSERT INTO buchungen (datum, platz, name) VALUES (?, ?, ?)', (heute, '1', 'testuse'))
        conn.commit()

def wochenansicht(df: pd.DataFrame, start, ende) -> pd.DataFrame:
    """Erstelle ein leeres Wochen-Dataframe und fülle es mit den vorhandenen Buchungen."""
    # Einlesen der Arbeitsplätze-Konfiguration aus Datei plaetze.json
    with open('plaetze.json', 'r') as f:
        config = json.load(f)
    plaetze = config['plaetze']

    # Erstellen des Datumsindex
    date_index = pd.date_range(start, ende)
    
    # Erstellen des leeren Wochen-DataFrames
    # aktuelle_woche = pd.DataFrame(columns=[str(i) for i in range(1, 9)], index=date_index)
    aktuelle_woche = pd.DataFrame(columns=plaetze, index=date_index)
    aktuelle_woche.index.names = ['datum']
    aktuelle_woche.columns.names = ['platz']
    # die eingelesenen schon gespeicherten buchungen werden mit dem leeren wochen-df kombiniert
    # df = df.reset_index()
    # datenfilter = df.between(start, ende)
    df = df.pivot(index='datum', columns='platz', values='name')
    df.columns.names = ['platz']
    aktuelle_woche = aktuelle_woche.combine_first(df)
    aktuelle_woche.fillna('', inplace=True)
    return aktuelle_woche

def main():
    # Streamlit App
    # fuege_beispieldaten_hinzu()
    
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    st.title('Arbeitsplatz-Buchungstool')
     # Ermitteln des aktuellen Arbeitsverzeichnisses
    aktuelles_verzeichnis = os.getcwd()
    st.write("Das aktuelle Arbeitsverzeichnis ist:", aktuelles_verzeichnis)
    # Kalenderwidget zur Auswahl des Zeitraums
    st.header('1. Datumsbereich wählen')
    col1, col2 = st.columns(2)
    with col1:
        start_datum = st.date_input('Startdatum', datetime.today(), format="DD.MM.YYYY", min_value=datetime.today()-timedelta(days=20), max_value=datetime.today() + timedelta(days=21))
    with col2:
        ende_datum = st.date_input('Enddatum', datetime.today() + timedelta(days=7), format="DD.MM.YYYY", min_value=datetime.today()-timedelta(days=20), max_value=datetime.today() + timedelta(days=21))
    
    if start_datum > ende_datum:
        st.error('Das Startdatum darf nicht nach dem Enddatum liegen!')
    elif start_datum < ende_datum: 
        # Buchungen für den gewählten Zeitraum laden
        buchungen_df = lade_buchungen(start_datum, ende_datum)

        wochen_df = wochenansicht(buchungen_df, start_datum, ende_datum)

    
        # Dataframe anzeigen und bearbeiten lassen
        st.header('2. Buchungen bearbeiten')
        data_editor = st.data_editor(
            wochen_df, column_config={
            "datum": st.column_config.DateColumn(
                "Datum",
                format="DD.MM.",
            ),
        }
        )

    st.header('3. Änderungen speichern')
    # Änderungen speichern
    if st.button('Änderungen speichern'):
        speichere_buchungen(data_editor)
        st.success('Buchungen erfolgreich gespeichert!')
    
    st.header('Arbeitsplatzübersicht')
    st.image('arbeitsplatz/grundriss.png', use_column_width=True)

if __name__ == "__main__":
    # Datenbankverbindung herstellen
    conn = sqlite3.connect('buchungen.db')
    c = conn.cursor()

    # Tabelle erstellen, falls sie noch nicht existiert
    c.execute('''
        CREATE TABLE IF NOT EXISTS buchungen (
            datum DATE,
            platz TEXT,
            name TEXT
        )
    ''')
    conn.commit()
    main()
    # Datenbankverbindung schließen
    conn.close()