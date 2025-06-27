import streamlit as st
import pandas as pd
import io
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import base64
from fpdf import FPDF
import tempfile
import os

# Fest hinterlegte Mutterliste laden (aus dem Projektverzeichnis)
@st.cache_data
def load_mutterliste():
    df = pd.read_excel("Herzstuecke-Mutter-Liste.xlsx")
    df = df[df["Artikel"].notna()].copy()
    df["Artikel"] = df["Artikel"].astype(str).str.strip().str.replace(".0", "", regex=False)
    return df

# Barcode generieren als Bilddatei (nicht base64)
def generate_barcode_image(code):
    CODE128 = barcode.get_barcode_class("code128")
    rv = io.BytesIO()
    try:
        barcode_obj = CODE128(code, writer=ImageWriter())
        barcode_obj.write(rv, options={"module_height": 10.0, "font_size": 8, "quiet_zone": 2.0})
        rv.seek(0)
        return Image.open(rv).convert("RGB")
    except Exception:
        return None

# PDF-Export mit Barcodes (kompakt, 3 Spalten optimiert, bessere Barcodequalität)
def generate_pdf(df):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Herzstücke - Fehlende Artikel (Negativliste)", ln=True, align="L")
    pdf.ln(5)

    tempfiles = []
    col_width = 62  # drei Spalten auf A4 (180mm nutzbar)
    row_height = 40
    margin = 10
    spacing = 3
    x_positions = [margin + i * col_width for i in range(3)]
    col = 0
    y = pdf.get_y()

    for index, row in df.iterrows():
        bezeichnung = str(row["Bezeichnung"])
        artikel = str(row["Artikel"])
        barcode_img = generate_barcode_image(artikel)

        if barcode_img:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                barcode_img.save(tmpfile.name, format="PNG")
                tempfiles.append(tmpfile.name)

                x = x_positions[col]
                if col == 0:
                    y = pdf.get_y()
                pdf.set_xy(x, y)
                pdf.set_font("Arial", style="B", size=7)
                pdf.multi_cell(col_width - spacing, 4, bezeichnung, border=0)
                pdf.set_xy(x, pdf.get_y())
                pdf.set_font("Arial", size=6)
                pdf.cell(col_width - spacing, 4, f"GTIN: {artikel}", ln=2)
                pdf.image(tmpfile.name, x=x + 5, y=pdf.get_y(), w=col_width - 10)

                col = (col + 1) % 3
                if col == 0:
                    pdf.ln(row_height)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
        pdf.output(pdf_tmp.name)
        with open(pdf_tmp.name, "rb") as f:
            pdf_bytes = f.read()

    for path in tempfiles:
        try:
            os.remove(path)
        except Exception:
            pass

    return pdf_bytes

st.title("🛒 Herzstücke Sortiments-Check")
st.markdown("""
Bitte laden Sie Ihre **Positivliste** hoch. Diese Anwendung vergleicht Ihre Liste mit dem vollständigen Herzstücke-Sortiment
und erstellt automatisch eine Negativliste mit Artikeln, die in Ihrem Markt fehlen.

**Hinweis:** Es wird erwartet, dass Ihre Positivliste eine Spalte `Artikel` enthält (GTIN/EAN).
""")

uploaded_file = st.file_uploader("Positivliste hochladen (.xlsx)", type=["xlsx"])

if uploaded_file:
    mutter_df = load_mutterliste()
    positiv_df = pd.read_excel(uploaded_file)

    if "Artikel" not in positiv_df.columns:
        st.error("Die hochgeladene Positivliste enthält keine Spalte 'Artikel'.")
    else:
        positiv_df = positiv_df[positiv_df["Artikel"].notna()].copy()
        positiv_df["Artikel"] = positiv_df["Artikel"].astype(str).str.strip().str.replace(".0", "", regex=False)
        mutter_df["Artikel"] = mutter_df["Artikel"].astype(str).str.strip().str.replace(".0", "", regex=False)
        mutter_artikel = set(mutter_df["Artikel"])
        positiv_artikel = set(positiv_df["Artikel"])

        fehlende_artikel = sorted(mutter_artikel - positiv_artikel)
        negativ_df = mutter_df[mutter_df["Artikel"].isin(fehlende_artikel)].copy()
        negativ_df = negativ_df[["Bezeichnung", "Artikel"]]

        st.success(f"{len(negativ_df)} Artikel fehlen in Ihrem Sortiment.")
        st.markdown("**Negativliste (Vorschau gekürzt):**")
        st.dataframe(negativ_df.head(20))
        st.caption("Es werden nur die ersten 20 Einträge angezeigt. Bitte laden Sie die vollständige Liste als PDF herunter.")

        pdf_file = generate_pdf(negativ_df)
        st.download_button(
            label="📄 Negativliste als PDF herunterladen",
            data=pdf_file,
            file_name="Herzstuecke-Negativliste.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.markdown("⚠️ **Hinweis:** Diese Anwendung speichert keine Daten und hat keinen Zugriff auf Ihre Dateien.")
st.markdown("🌟 **Erstellt von Christoph R. Kaiser mit Hilfe von Künstlicher Intelligenz.**")
