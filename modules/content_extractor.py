import pdfplumber
from PyPDF2 import PdfReader


def get_page_count(pdf_path):
    reader = PdfReader(pdf_path)
    return len(reader.pages)


def extract_all_content(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            full_text += f"\n=== PAGE {i} ===\n{text}\n"
    return full_text


def extract_in_chunks(pdf_path, pages_per_chunk=25):
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for start in range(0, total_pages, pages_per_chunk):
            end = min(start + pages_per_chunk, total_pages)
            chunk_text = ""
            for i in range(start, end):
                text = pdf.pages[i].extract_text() or ""
                chunk_text += f"\n=== PAGE {i+1} ===\n{text}\n"
            chunks.append({
                "chunk_number": len(chunks) + 1,
                "start_page": start + 1,
                "end_page": end,
                "content": chunk_text
            })
    return chunks


def extract_tables(pdf_path):
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if tables:
                all_tables.append({"page": i, "tables": tables})
    return all_tables


def chunk_plain_text(text, words_per_chunk=4500):
    """
    যেকোনো প্লেইন টেক্সট (PDF + পেস্ট করা টেক্সট + URL থেকে আসা টেক্সট মিলিয়ে)
    নির্দিষ্ট শব্দ-সংখ্যা অনুযায়ী chunk এ ভাগ করে। PDF না থাকলেও কাজ করবে।
    """
    words = text.split()
    chunks = []
    total_words = len(words)

    for start in range(0, total_words, words_per_chunk):
        end = min(start + words_per_chunk, total_words)
        chunk_words = words[start:end]
        chunks.append({
            "chunk_number": len(chunks) + 1,
            "content": " ".join(chunk_words)
        })

    if not chunks:
        chunks.append({"chunk_number": 1, "content": text})

    return chunks