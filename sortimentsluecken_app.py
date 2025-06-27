import streamlit as st
import pandas as pd
import io
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import base64

# Fest hinterlegte Mutterliste laden (aus dem Projektverzeichnis)
@st.cache_data
def load_mutterliste():
    df = pd.read_excel("Herzstuecke-Mutter-Liste.xlsx")
    df["Artikel"] = df["Artikel"].astype(str).str.strip()
    return df

# Funktion zur Erzeugung eines Barcodes als Base64-String
def generate_barcode_base64(code):
    CODE128 = barcode.get_barcode_class('code128')
    rv = io.BytesIO()
    try:
        CODE128(code, writer=ImageWriter()).write(rv)
        encoded = base64.b64encode(rv.getvalue()).decode("utf-8")
        return f"<img src='data:image/png;base64,{encoded}' width='150'>"
    except Exception:
        return "Fehler"

st.title("🛒 Herzstücke Sortiments-Check")
st.markdown("""
Lade deine **Positivliste** hoch. Die App vergleicht sie mit dem Herzstücke-Gesamtsortiment
und erstellt automatisch eine Negativliste (fehlende Artikel in deinem Markt).

**Hinweis:** Es wird erwartet, dass die Positivliste eine Spalte `Artikel` enthält (GTIN/EAN).
""")

uploaded_file = st.file_uploader("Positivliste hochladen (.xlsx)", type=["xlsx"])

if uploaded_file:
    mutter_df = load_mutterliste()
    positiv_df = pd.read_excel(uploaded_file)

    if "Artikel" not in positiv_df.columns:
        st.error("Die hochgeladene Positivliste enthält keine Spalte 'Artikel'.")
    else:
        # Vergleich vorbereiten
        positiv_df["Artikel"] = positiv_df["Artikel"].astype(str).str.strip()
        mutter_df["Artikel"] = mutter_df["Artikel"].astype(str).str.strip()
        mutter_artikel = set(mutter_df["Artikel"])
        positiv_artikel = set(positiv_df["Artikel"])

        fehlende_artikel = sorted(mutter_artikel - positiv_artikel)
        negativ_df = mutter_df[mutter_df["Artikel"].isin(fehlende_artikel)].copy()

        # Barcode-Spalte erzeugen (HTML fähig)
        negativ_df["Barcode"] = negativ_df["Artikel"].apply(generate_barcode_base64)

        # Spaltenreihenfolge ändern: Bezeichnung, Artikel, Barcode
        negativ_df = negativ_df[["Bezeichnung", "Artikel", "Barcode"]]

        st.success(f"{len(negativ_df)} Artikel fehlen im Sortiment.")
        st.markdown("**Negativliste mit Barcodes:**", unsafe_allow_html=True)
        st.write(negativ_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Download-Button für Negativliste (ohne HTML)
        @st.cache_data
        def convert_df(df):
            df_clean = df.drop(columns=["Barcode"])
            output = io.BytesIO()
            df_clean.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)
            return output

        excel_data = convert_df(negativ_df)
        st.download_button(
            label="📥 Negativliste herunterladen",
            data=excel_data,
            file_name="Herzstuecke-Negativliste.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")
st.markdown("⚠️ **Hinweis:** Diese Anwendung speichert keine Daten und hat keinen Zugriff auf Ihre Dateien.")
st.markdown("🌟 **Erstellt von Christoph R. Kaiser mit Hilfe von Künstlicher Intelligenz.**")
