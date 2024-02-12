import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Datenbankverbindung herstellen
conn = sqlite3.connect('buchungen.db')
c = conn.cursor()

# Tabelle erstellen, falls sie noch nicht existiert
c.execute('''
    CREATE TABLE IF NOT EXISTS buchungen (
        datum DATE,
        platz INTEGER,
        name TEXT
    )
''')
conn.commit()

# Hilfsfunktion zum Laden der Buchungen aus der Datenbank
def lade_buchungen(start, ende):
    c.execute('SELECT * FROM buchungen WHERE datum BETWEEN ? AND ?', (start, ende))
    buchungen = pd.DataFrame(c.fetchall(), columns=['datum', 'platz', 'name'])
    buchungen['datum'] = pd.to_datetime(buchungen['datum'])
    return buchungen

# Hilfsfunktion zum Speichern der Buchungen in der Datenbank
def speichere_buchungen(df):
    f"index min: {df.index.min()}, max: {df.index.max()}"
    c.execute('DELETE FROM buchungen WHERE datum BETWEEN ? AND ?', (df.index.min(), df.index.max()))
    for datum, row in df.iterrows():
        for platz, name in enumerate(row, start=1):
            if pd.notnull(name):
                c.execute('INSERT INTO buchungen (datum, platz, name) VALUES (?, ?, ?)', (datum.date(), platz, name))
    conn.commit()

# Beispieldaten hinzufügen, wenn die Tabelle leer ist
def fuege_beispieldaten_hinzu():
    heute = datetime.today().date()
    c.execute('SELECT * FROM buchungen WHERE datum = ?', (heute,))
    if not c.fetchall():
        c.execute('INSERT INTO buchungen (datum, platz, name) VALUES (?, ?, ?)', (heute, 1, 'testuse'))
        conn.commit()

fuege_beispieldaten_hinzu()

# Streamlit App
st.title('Arbeitsplatz-Buchungstool')

# Kalenderwidget zur Auswahl des Zeitraums
start_datum = st.date_input('Startdatum', datetime.today())
ende_datum = st.date_input('Enddatum', datetime.today() + timedelta(days=7))

# Buchungen für den gewählten Zeitraum laden
buchungen_df = lade_buchungen(start_datum, ende_datum)

# Dataframe für die Anzeige vorbereiten
alle_datums = pd.date_range(start_datum, ende_datum, freq='D')
buchungen_df = buchungen_df.pivot(index='datum', columns='platz', values='name')
buchungen_df = buchungen_df.reindex(alle_datums, fill_value='')

# Dataframe anzeigen und bearbeiten lassen
st.data_editor(buchungen_df)

# Änderungen speichern
if st.button('Änderungen speichern'):
    speichere_buchungen(buchungen_df)
    st.success('Buchungen erfolgreich gespeichert!')

# Datenbankverbindung schließen
conn.close()