"""
# VTP Reader & Info Extractor
"""

# Imports
import fitz
import pandas as pd
import streamlit as st


# Classes
# Imports
import re
import fitz
import pandas as pd


# Classes
class PDF:
    def __init__(self, filepath):
        """
        PDF Document class that reads/parses a pdf file and contains the document itself and its metadata
        :param filepath: str - path to the pdf file
        """
        self.fname = filepath
        self.doc = fitz.open(filepath)
        self.page_count = self.doc.page_count
        self.meta_data = self.doc.metadata


class VTP:
    def __init__(self, vtp_filepath):
        """
        VTP Document class - Uses PDF class to parse the pdf file and perform validity checks and extracts information
        :param vtp_filepath: str - path to the vtp file
        """
        self.fname = vtp_filepath
        self.document = PDF(vtp_filepath)
        self.checks = {'page_check': False, 'title_check': False, 'format_check': False, 'producer_check': False, 'non_tampered_check': False}

    def basic_checks(self):
        """
        Perform basic checks on the VTP document using metadata
        :return: bool(passed) - Whether the validity checks have been passed or not
        """
        if (self.document.page_count == 4) or (self.document.page_count == 1):          # First page/Full document
            self.checks['page_check'] = True
        if self.document.meta_data["title"] == "VTL Approval Letter":                   # PDF Title check
            self.checks['title_check'] = True
        if self.document.meta_data["format"] == 'PDF 1.4':                              # PDF Format check
            self.checks['format_check'] = True
        if self.document.meta_data["producer"] == "iText 2.1.7 by 1T3XT":               # PDF Producer check
            self.checks['producer_check'] = True
        if self.document.meta_data["creationDate"] == self.document.meta_data["modDate"]:  # Created & Modified date check
            self.checks['non_tampered_check'] = True
        return all(self.checks.values())

    def extract_info(self):
        """
        Check the validity of the pdf and extract fields of interest
        :return: dict(result) - Dictionary of entities and values (or dict with error)
        """
        if not self.basic_checks():
            return {'Error': 'Validity Checks Failed'}
        page = self.document.doc.load_page(0)                                           # Read first page
        blocks = page.get_text("blocks")                                                # Extract & Process text
        blocks = [block[4] for block in blocks]
        blocks = [block.strip() for block in blocks if len(block.strip()) > 3]

        # Check Air VTL
        all_text = " ".join(blocks)
        vtl_mentions = re.findall("VTL \(.*?\)", all_text)
        vtp_mentions = re.findall("VTP \(.*?\)", all_text)
        if len(list(set(vtl_mentions))) != 1:
            return {'Error': 'Validity Checks Failed'}
        if len(list(set(vtp_mentions))) != 1:
            return {'Error': 'Validity Checks Failed'}
        vtl_type = list(set(vtl_mentions))[0]
        vtp_type = list(set(vtp_mentions))[0]

        # Extract entities based on position
        vtp_date, ref_number, name, fin_number, passport_number, from_date, to_date = "", "", "", "", "", "", ""
        for i in range(3):
            text = blocks[i]
            if text.startswith("Date"):
                vtp_date = text.split()[1].strip()
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

        # Construct Dataframe
        fields = ['VTP Type', 'VTL Type', 'VTP Issue Date', 'VTP Reference Number', 'Name', 'FIN Number', 'Passport Number', 'VTP Valid From', 'VTP Valid To']
        values = [vtp_type, vtl_type, vtp_date, ref_number, name, fin_number, passport_number, from_date, to_date]
        result = pd.DataFrame({"Entity": fields, "VALUE": values})
        return dict(zip(result["Entity"], result["VALUE"]))


# Streamlit App
"""
# VTP Reader & Info Extractor
"""
document_file = st.file_uploader("Upload VTP Document", type="pdf")
if document_file is not None:
    with open(document_file.name, "wb") as dfh:
        dfh.write(document_file.getbuffer())
        st.success("File Upload Successfull")
    with st.spinner("Extracting Info from VTP... Please Wait..."):
        vtp_doc = VTP(document_file.name)
    st.write(vtp_doc.extract_info())

