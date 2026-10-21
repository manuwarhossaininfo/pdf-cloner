"""
Style Analyzer Module (No File Upload - Direct Text Reading)
--------------------------------------------------------------
"""

import google.generativeai as genai
import pdfplumber
import json


def analyze_style_to_json(api_key: str, model_name: str, sample_pdf_path: str) -> dict:
    """
    Sample PDF থেকে সরাসরি টেক্সট পড়ে style বিশ্লেষণ করে।
    """
    clean_api_key = api_key.strip()
    genai.configure(api_key=clean_api_key)
    model = genai.GenerativeModel(model_name)
    
    # PDF থেকে text বের করা (এখানে কোনো upload_file নেই)
    sample_text = ""
    try:
        with pdfplumber.open(sample_pdf_path) as pdf:
            pages_to_read = min(len(pdf.pages), 20)
            for i in range(pages_to_read):
                text = pdf.pages[i].extract_text()
                if text:
                    sample_text += f"\n--- Page {i+1} ---\n" + text
    except Exception:
        sample_text = "No text could be extracted from sample."

    prompt = f"""
You are an expert document design analyst.
Analyze this sample document text and create a style blueprint as JSON.

SAMPLE DOCUMENT TEXT:
{sample_text[:15000]}

Return ONLY a valid JSON object (no markdown formatting) with this structure:

{{
  "document_type": "report",
  "language": "bengali",
  "page_setup": {{
    "size": "A4",
    "orientation": "portrait",
    "margin_top": "2cm",
    "margin_bottom": "2cm",
    "margin_left": "2cm",
    "margin_right": "2cm"
  }},
  "color_scheme": {{
    "primary": "#2C3E50",
    "secondary": "#3498DB",
    "accent": "#E74C3C",
    "text": "#333333",
    "background": "#FFFFFF"
  }},
  "typography": {{
    "body_font": "Helvetica",
    "body_size": "10pt",
    "body_line_height": "1.5",
    "heading_font": "Helvetica",
    "h1_size": "22pt",
    "h1_weight": "bold",
    "h1_color": "#2C3E50",
    "h2_size": "16pt",
    "h2_color": "#3498DB",
    "h3_size": "13pt"
  }},
  "tables": {{
    "border_style": "solid",
    "border_color": "#DDDDDD",
    "header_background": "#2C3E50",
    "header_text_color": "#FFFFFF"
  }}
}}

Return ONLY valid JSON. No extra text.
"""
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()
    
    try:
        blueprint = json.loads(raw_text)
        return blueprint
    except json.JSONDecodeError:
        return _get_default_blueprint()


def _get_default_blueprint() -> dict:
    return {
        "document_type": "report",
        "language": "bengali",
        "page_setup": {
            "size": "A4",
            "orientation": "portrait",
            "margin_top": "2cm",
            "margin_bottom": "2cm",
            "margin_left": "2cm",
            "margin_right": "2cm"
        },
        "color_scheme": {
            "primary": "#2C3E50",
            "secondary": "#3498DB",
            "accent": "#E74C3C",
            "text": "#333333",
            "background": "#FFFFFF"
        },
        "typography": {
            "body_font": "Helvetica",
            "body_size": "10pt",
            "body_line_height": "1.5",
            "heading_font": "Helvetica",
            "h1_size": "22pt",
            "h1_weight": "bold",
            "h1_color": "#2C3E50",
            "h2_size": "16pt",
            "h2_color": "#3498DB",
            "h3_size": "13pt"
        },
        "tables": {
            "border_style": "solid",
            "border_color": "#DDDDDD",
            "header_background": "#2C3E50",
            "header_text_color": "#FFFFFF"
        }
    }