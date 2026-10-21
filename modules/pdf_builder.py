import google.generativeai as genai
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from modules.style_template import get_full_css


def generate_notes_html(api_key, model_name, content_text, chunk_info=""):
    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel(model_name)

    prompt = f"""
তুমি একজন এক্সপার্ট নোট-মেকার। নিচের কন্টেন্ট থেকে একটি কমপ্যাক্ট, পরীক্ষা-উপযোগী নোট বানাতে হবে।
আউটপুট শুধুমাত্র HTML fragment হবে — <html>, <head>, <style>, বা markdown কোড ফেন্স (```) থাকবে না।

শুধু এই ক্লাসগুলো ব্যবহার করবে:
- <div class="topic-section"> ... </div>  → প্রতিটা টপিক/সাব-টপিক পুরোটা (title+content) এর ভেতরে থাকবে
- <div class="topic-title">টপিকের নাম</div>
- <div class="sub-heading">সাব-হেডিং</div>
- <ul class="fact-list"><li><span class="key-term">টার্ম</span>- ব্যাখ্যা, <span class="highlight">সংখ্যা/নাম</span></li></ul>
- <div class="sub-point">অতিরিক্ত ব্যাখ্যা</div>
- <table class="info-table">...</table>  → তুলনামূলক/শ্রেণীবদ্ধ তথ্যের জন্য বাধ্যতামূলক
- <div class="flow-diagram"><div class="flow-box">ধাপ ১</div><div class="flow-arrow">↓</div><div class="flow-box">ধাপ ২</div></div>  → ধারাবাহিক প্রক্রিয়া/হায়ারার্কির জন্য বাধ্যতামূলক

কঠোর নিয়ম:
1. কোনো প্যারাগ্রাফ হুবহু কপি না করে, ছোট ছোট "টার্ম- উত্তর" বুলেটে ভাঙবে।
2. তুলনামূলক/শ্রেণীবদ্ধ তথ্য অবশ্যই টেবিলে দিবে।
3. ধারাবাহিক প্রক্রিয়া/স্তরবিন্যাস অবশ্যই flow-diagram এ দিবে।
4. সকল সংখ্যা/তারিখ/নাম অবশ্যই <span class="highlight"> দিয়ে হাইলাইট করবে।
5. একটা তথ্যও বাদ দেওয়া যাবে না, কিছুই সামারি করা যাবে না।
6. প্রতিটা টপিক <div class="topic-section"> দিয়ে মোড়ানো থাকবে।
7. টপিকগুলোর মাঝে কোনো page-break বা ফাঁকা জায়গা দিবে না — একটা শেষ হলে সাথে সাথে পরেরটা শুরু হবে, এটা সিস্টেম নিজেই সামলাবে।
8. আউটপুট শুধু raw HTML fragment।

{chunk_info}

কন্টেন্ট:
{content_text}
"""

    response = model.generate_content(prompt)
    html_fragment = response.text.strip()

    if html_fragment.startswith("```"):
        html_fragment = html_fragment.strip("`")
        html_fragment = html_fragment.replace("html", "", 1).strip()

    return html_fragment


def build_final_html(brand_name, author_name, body_fragments):
    css = get_full_css()

    header_html = f'<div id="page-header">[{brand_name}] Prepared by: [{author_name}]</div>'
    footer_html = f'<div id="page-footer">{brand_name} | {author_name}</div>'

    cover_html = f"""
    <div class="cover-page">
        <div class="cover-title">{brand_name}</div>
        <div class="cover-sub">Prepared by: {author_name}</div>
    </div>
    <div class="page-break"></div>
    """

    # টপিকগুলোর মাঝে কোনো page-break ছাড়াই সরাসরি জোড়া — জায়গা নষ্ট হবে না
    body_combined = "\n".join(body_fragments)

    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>{css}</style>
    </head>
    <body>
        {header_html}
        {footer_html}
        {cover_html}
        {body_combined}
    </body>
    </html>
    """

    return final_html


def convert_html_to_pdf(html_code, output_path):
    font_config = FontConfiguration()
    HTML(string=html_code).write_pdf(output_path, font_config=font_config)
    return output_path