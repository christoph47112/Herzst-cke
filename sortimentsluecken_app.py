import streamlit as st
import pandas as pd
import io

# Fest hinterlegte Mutterliste laden (aus dem Projektverzeichnis)
@st.cache_data
def load_mutterliste():
    df = pd.read_excel("Herzstuecke-Mutter-Liste.xlsx")
    df["Artikel"] = df["Artikel"].astype(str).str.strip()
    return df

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
        mutter_artikel = set(mutter_df["Artikel"])
        positiv_artikel = set(positiv_df["Artikel"])

        fehlende_artikel = sorted(mutter_artikel - positiv_artikel)
        negativ_df = mutter_df[mutter_df["Artikel"].isin(fehlende_artikel)]

        st.success(f"{len(negativ_df)} Artikel fehlen im Sortiment.")
        st.dataframe(negativ_df)

        # Download-Button für Negativliste
        @st.cache_data
        def convert_df(df):
            output = io.BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
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
