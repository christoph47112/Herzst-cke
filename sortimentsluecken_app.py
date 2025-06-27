import streamlit as st
import pandas as pd

# Fest hinterlegte Mutterliste laden (aus dem Projektverzeichnis)
@st.cache_data
def load_mutterliste():
    return pd.read_excel("Herzstuecke-Mutter-Liste.xlsx")

# Upload der Positivliste durch den Benutzer
st.title("🛒 Herzstücke Sortiments-Check")
st.markdown("Lade hier deine **Positivliste** hoch. Die App vergleicht sie mit dem Gesamtsortiment und erstellt automatisch eine Negativliste (Sortimentslücken).")

uploaded_file = st.file_uploader("Positivliste hochladen (.xlsx)", type=["xlsx"])

if uploaded_file:
    mutter_df = load_mutterliste()
    positiv_df = pd.read_excel(uploaded_file)

    # Vereinfachter Vergleich über GTIN (kann angepasst werden)
    mutter_gtins = mutter_df["GTIN"].astype(str).unique()
    positiv_gtins = positiv_df["GTIN"].astype(str).unique()

    fehlende_gtins = sorted(set(mutter_gtins) - set(positiv_gtins))
    negativ_df = mutter_df[mutter_df["GTIN"].astype(str).isin(fehlende_gtins)]

    st.success(f"{len(negativ_df)} Artikel fehlen im Sortiment.")
    st.dataframe(negativ_df)

    # Download-Button für Negativliste
    @st.cache_data
    def convert_df(df):
        return df.to_excel(index=False, engine="openpyxl")

    excel_data = convert_df(negativ_df)
    st.download_button(
        label="📥 Negativliste herunterladen",
        data=excel_data,
        file_name="Herzstuecke-Negativliste.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
