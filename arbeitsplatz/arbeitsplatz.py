import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, date
from sqlalchemy.sql import text



# def daten_laden() -> pd.DataFrame:
#     df = pd.read_csv("buchungen.csv")
#     df.datum = pd.to_datetime(df.datum)
#     df = df.pivot(index='datum', columns='platz', values='name')
#     return df

def init_db(conn):
    with conn.session as s:
        data = [
                {"datum":"2024-01-24","platz":5,"name":"SK"},
                {"datum":"2024-01-24","platz":4,"name":"MH"},
                {"datum":"2024-02-02","platz":1,"name":"AW"},
                {"datum":"2024-02-05","platz":2,"name":"BR"},
                {"datum":"2024-02-02","platz":2,"name":"BR"},
                {"datum":"2024-02-06","platz":7,"name":"IWS"},
                {"datum":"2024-02-07","platz":4,"name":"JR"}
            ]
        s.execute(text("CREATE TABLE IF NOT EXISTS bookings (datum DATE, platz INTEGER, name TEXT)"))
        s.execute(
            text("INSERT INTO bookings (datum, platz, name) VALUES (:datum, :platz, :name)"), data
        )
        s.commit()


def build_woche(df: pd.DataFrame, selected_dates: tuple) -> pd.DataFrame:
    # Erstellen des Datumsindex
    date_index = pd.date_range(selected_dates[0], selected_dates[1])
    # Erstellen des leeren Wochen-DataFrames
    aktuelle_woche = pd.DataFrame(columns=range(1, 9), index=date_index)
    aktuelle_woche.index.names = ['datum']
    aktuelle_woche.columns.names = ['platz']
    # die eingelesenen schon gespeicherten buchungen werden mit dem leeren wochen-df kombiniert
    # df = df.reset_index()
    datenfilter = df.between(selected_dates[0], selected_dates[1])
    return aktuelle_woche.combine_first(df.loc[datenfilter])

def read_selection(conn, selected_dates):
    auswahl = conn.query(f'select * from bookings where datum BETWEEN {selected_dates[0].strftime("%Y-%m-%d")} AND {selected_dates[1].strftime("%Y-%m-%d")}')
    return auswahl

def get_current_week_dates():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday

def main():
    conn = st.connection('bookings_db', type='sql')
    # init_db(conn)
    # buchungen = conn.query('select * from bookings')
    # st.dataframe(buchungen)
    #gesamt = daten_laden()

    # Get the current week's Monday and Friday
    monday, friday = get_current_week_dates()
    
    # Create the datepicker with the preset dates
    selected_dates = st.date_input(
        "Wählen Sie ein Datum",
        value=(monday, friday),
        format="DD.MM.YYYY"  # German date format
    )
    selected_dates
    read_selection(conn, selected_dates)
    # st.data_editor(build_woche(gesamt, selected_dates))

if __name__ == "__main__":
    main()