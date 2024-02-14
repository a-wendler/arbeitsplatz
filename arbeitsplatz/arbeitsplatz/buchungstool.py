import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Hilfsfunktion zum Laden der Buchungen aus der Datenbank
def lade_buchungen(start, ende):
    c.execute('SELECT * FROM buchungen WHERE datum BETWEEN ? AND ?', (start, ende))
    buchungen = pd.DataFrame(c.fetchall(), columns=['datum', 'platz', 'name'])
    buchungen['datum'] = pd.to_datetime(buchungen['datum'])
    return buchungen

# Hilfsfunktion zum Speichern der Buchungen in der Datenbank
def speichere_buchungen(df):
    
    # st.header("Spalten")
    # df.columns
    # st.session_state['mein_dataframe'].columns

    # st.header("Index")
    # df.index
    # st.session_state['mein_dataframe'].index
    # st.write("ENDE")

    # Unterschiede finden
    # diff_mask = st.session_state.mein_dataframe != df

    # # Nur unterschiedliche Werte behalten
    # diff_df = st.session_state.mein_dataframe.where(diff_mask, other=None)
    # st.header("diff_df")
    # diff_df

    c.execute('DELETE FROM buchungen WHERE datum BETWEEN ? AND ?', (df.index.min().strftime('%Y-%m-%d'), df.index.max().strftime('%Y-%m-%d')))
    for datum, row in df.iterrows():
        for platz, name in enumerate(row, start=1):
            if pd.notnull(name):
                c.execute('INSERT INTO buchungen (datum, platz, name) VALUES (?, ?, ?)', (datum.date().strftime('%Y-%m-%d'), platz, name))
    conn.commit()

# Beispieldaten hinzufügen, wenn die Tabelle leer ist
def fuege_beispieldaten_hinzu():
    heute = datetime.today().date()
    c.execute('SELECT * FROM buchungen WHERE datum = ?', (heute,))
    if not c.fetchall():
        c.execute('INSERT INTO buchungen (datum, platz, name) VALUES (?, ?, ?)', (heute, '1', 'testuse'))
        conn.commit()

def wochenansicht(df: pd.DataFrame, start, ende) -> pd.DataFrame:
    # Erstellen des Datumsindex
    date_index = pd.date_range(start, ende)
    # Erstellen des leeren Wochen-DataFrames
    aktuelle_woche = pd.DataFrame(columns=[str(i) for i in range(1, 9)], index=date_index)
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

    st.title('Arbeitsplatz-Buchungstool')
    
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
    st.image('grundriss.png', use_column_width=True)

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