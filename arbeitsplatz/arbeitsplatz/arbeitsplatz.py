import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, date

def daten_laden() -> pd.DataFrame:
    df = pd.read_csv("buchungen.csv")
    df.datum = pd.to_datetime(df.datum)
    df = df.pivot(index='datum', columns='platz', values='name')
    return df

def build_woche(df: pd.DataFrame, selected_dates: tuple) -> pd.DataFrame:
    # Erstellen des Datumsindex
    date_index = pd.date_range(datetime.now().date(), periods=5, freq='B')
    # Erstellen des leeren Wochen-DataFrames
    aktuelle_woche = pd.DataFrame(columns=range(1, 9), index=date_index)
    aktuelle_woche.index.names = ['datum']
    aktuelle_woche.columns.names = ['platz']
    # die eingelesenen schon gespeicherten buchungen werden mit dem leeren wochen-df kombiniert
    return aktuelle_woche.combine_first(df)

def get_current_week_dates():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday

def main():
    gesamt = daten_laden()

    # Get the current week's Monday and Friday
    monday, friday = get_current_week_dates()
    # Create the datepicker with the preset dates
    selected_dates = st.date_input(
        "Wählen Sie ein Datum",
        value=(monday, friday),
        format="DD.MM.YYYY"  # German date format
    )

    st.data_editor(build_woche(gesamt))

if __name__ == "__main__":
    main()