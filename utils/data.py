from pathlib import Path
import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "simulated_emergencies.csv"

@st.cache_data(show_spinner=False)
def load_demo_dataset():
    if not DATA_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(DATA_FILE)
