"""
# VTP Reader & Info Extractor
"""

# Imports
import fitz
import pandas as pd
import streamlit as st


# Classes
class PDFdocument:
    def __init__(self, fname):
        self.fname = fname
        self.doc = fitz.open(fname)
        self.page_count = self.doc.page_count
        self.meta_data = self.doc.metadata


# Streamlit App
"""
# VTP Reader & Info Extractor
"""
document_file = st.file_uploader("Upload VTP Document", type="pdf")
if document_file is not None:
    with open(document_file.name, "wb") as dfh:
        dfh.write(document_file.getbuffer())
        st.success("File Upload Successfull")
    document = PDFdocument(document_file.name)
    page = document.doc.load_page(0)
    blocks = page.get_text("blocks")
    blocks = [block[4] for block in blocks]
    blocks = [block.strip() for block in blocks if len(block.strip()) > 3]
    ref_number, name, fin_number, passport_number, from_date, to_date = "", "", "", "", "", ""
    for i in range(3):
        text = blocks[i]
        if text.startswith("Date"):
            ref_number = text.split()[-1]
            break
    for i in range(2, 5):
        text = blocks[i]
        if text.startswith("Dear"):
            name = " ".join(text.split()[1:])
            if blocks[i+1].startswith("FIN"):
                fin_number = blocks[i+1].split()[-1]
            if blocks[i+2].startswith("Passport"):
                passport_number = blocks[i+2].split()[-1]
            break
    for i in range(6, 9):
        text = blocks[i]
        if text.startswith("Vaccinated Travel Lane (Air)"):
            from_date = text.split()[-3]
            to_date = text.split()[-2]
            break
    fields = ['VTP Reference Number', 'Name', 'FIN Number', 'Passport Number', 'From', 'To']
    values = [ref_number, name, fin_number, passport_number, from_date, to_date]
    result = pd.DataFrame({"Entity": fields, "VALUE": values})
    st.write(result)
