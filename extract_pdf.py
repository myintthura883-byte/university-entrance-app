import fitz  # PyMuPDF
import os

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text()
        full_text += text + "\n"
    return full_text

if __name__ == "__main__":
    pdf_path = "./data/pdfs/university.pdf"
    text = extract_text_from_pdf(pdf_path)
    print(text[:500])  # Check first 500 chars of extracted text
