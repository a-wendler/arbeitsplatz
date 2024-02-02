import pandas as pd
import streamlit as st
import datetime

def daten_laden() -> pd.DataFrame:
    df = pd.read_csv("buchungen.csv")
    df.datum = pd.to_datetime(df.datum)
    df = df.pivot(index='datum', columns='platz', values='name')
    return df

def build_woche(df) -> pd.DataFrame:
    # Erstellen des Datumsindex
    date_index = pd.date_range(datetime.datetime.now().date(), periods=5, freq='B')
    # Erstellen des leeren Wochen-DataFrames
    aktuelle_woche = pd.DataFrame(columns=range(1, 9), index=date_index)
    aktuelle_woche.index.names = ['datum']
    aktuelle_woche.columns.names = ['platz']
    # die eingelesenen schon gespeicherten buchungen werden mit dem leeren wochen-df kombiniert
    return aktuelle_woche.combine_first(df)


df = daten_laden()
st.data_editor(build_woche(df))