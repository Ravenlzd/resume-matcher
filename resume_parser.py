import pdfplumber
from io import BytesIO
from pdfminer.high_level import extract_text as pdfminer_extract_text

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF with a fallback path for hard-to-parse files.
    """
    raw = pdf_file.read()

    # Primary extractor: pdfplumber
    text = ""
    with pdfplumber.open(BytesIO(raw)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text += t + "\n"
    text = text.strip()

    # Fallback extractor: pdfminer (helps with some PDFs where pdfplumber is sparse)
    if len(text) < 200:
        try:
            fallback = pdfminer_extract_text(BytesIO(raw)).strip()
            if len(fallback) > len(text):
                text = fallback
        except Exception:
            pass

    return text
