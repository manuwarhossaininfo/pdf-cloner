import time
import google.generativeai as genai
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from modules.style_template import get_full_css

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

GENERATION_CONFIG = {
    "temperature": 0.3,
    "max_output_tokens": 8192,
}


def _safe_extract_text(response):
    """
    response.text ব্যবহার না করে, সরাসরি candidate.content.parts থেকে টেক্সট বের করে আনে।
    এতে citation_metadata parsing bug ('too many values to unpack') এড়ানো যায়।
    """
    if not response.candidates:
        raise RuntimeError("Gemini কোনো candidate রিটার্ন করেনি (সম্ভবত safety block)।")

    candidate = response.candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)

    text = ""
    try:
        for part in candidate.content.parts:
            if hasattr(part, "text") and part.text:
                text += part.text
    except Exception as e:
        raise RuntimeError(f"Response parts পড়তে সমস্যা হয়েছে: {e}")

    return text.strip(), finish_reason


def generate_notes_html(api_key, model_name, content_text, chunk_info="", custom_instruction="", max_retries=3):
    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel(
        model_name,
        safety_settings=SAFETY_SETTINGS,
        generation_config=GENERATION_CONFIG,
    )

    custom_instruction_block = ""
    if custom_instruction.strip():
        custom_instruction_block = f"""
=== ব্যবহারকারীর বিশেষ নির্দেশনা (এটা মেনে চলা বাধ্যতামূলক, কিন্তু নিচের মূল স্টাইল-ক্লাস গুলো ভাঙা যাবে না) ===
{custom_instruction.strip()}
"""

    prompt = f"""
তুমি একজন অভিজ্ঞ এক্সপার্ট নোট-মেকার, যে পরীক্ষার্থীদের জন্য কমপ্যাক্ট কিন্তু অত্যন্ত ডিটেইলড নোট বানায়।
আউটপুট শুধুমাত্র HTML fragment হবে — <html>, <head>, <style>, বা markdown কোড ফেন্স (```) থাকবে না।

শুধু এই ক্লাসগুলো ব্যবহার করবে:
- <div class="topic-section"> ... </div>  → প্রতিটা টপিক/সাব-টপিক পুরোটা (title+content) এর ভেতরে থাকবে
- <div class="topic-title">টপিকের নাম</div>
- <div class="sub-heading">সাব-হেডিং</div>
- <ul class="fact-list"><li><span class="key-term">টার্ম</span>- ব্যাখ্যা, <span class="highlight">সংখ্যা/নাম</span></li></ul>
- <div class="sub-point">অতিরিক্ত ব্যাখ্যা</div>
- <table class="info-table">...</table>  → তুলনামূলক/শ্রেণীবদ্ধ তথ্যের জন্য বাধ্যতামূলক
- <div class="flow-diagram"><div class="flow-box">ধাপ ১</div><div class="flow-arrow">↓</div><div class="flow-box">ধাপ ২</div></div>  → ধারাবাহিক প্রক্রিয়া/হায়ারার্কির জন্য বাধ্যতামূলক

=== সবচেয়ে গুরুত্বপূর্ণ নিয়ম (Information Loss একদম চলবে না) ===
1. সোর্স কন্টেন্টে থাকা প্রতিটা তথ্য, সংখ্যা, তারিখ, নাম, সংজ্ঞা, কারণ, ফলাফল, উদাহরণ — সবকিছু নোটে থাকতেই হবে। কোনো অজুহাতে কিছু সামারি/স্কিপ/শর্টকাট করা যাবে না।
2. একটা প্যারাগ্রাফে যদি ৫টা তথ্য থাকে, আউটপুটেও ৫টা আলাদা বুলেট পয়েন্ট থাকতে হবে — একটাও মিস করা যাবে না।
3. যদি কোনো তথ্য/সংজ্ঞা/ব্যাখ্যা একটু কম স্পষ্ট মনে হয়, তাহলে নিজের জ্ঞান দিয়ে অতিরিক্ত sub-point (ছোট ব্যাখ্যা) যোগ করে পাঠকের বোঝা সহজ করে দিবে — কিন্তু সোর্সের কোনো তথ্য বাদ দেওয়া যাবে না, শুধু যোগ করা যাবে।
4. মূল উদ্দেশ্য: এই নোট পড়েই যেন একজন স্টুডেন্ট মূল বই/সোর্স আর না পড়েও পরীক্ষায় সব উত্তর দিতে পারে — তাই ডিটেইল কমানো যাবে না, বরং দরকার হলে বাড়িয়ে দিবে।

=== MCQ হ্যান্ডলিং নিয়ম ===
যদি সোর্সে MCQ প্রশ্ন (প্রশ্ন + a/b/c/d অপশন + উত্তর) থাকে, তাহলে সেটাকে অপশনসহ না রেখে একটা তথ্যবহুল সরল লাইনে রূপান্তর করবে:

উদাহরণ —
সোর্স:
"বাংলাদেশের জাতীয় ফুল কোনটি? a) গোলাপ b) শাপলা c) জবা d) সূর্যমুখী  উত্তর: b"
রূপান্তরিত আউটপুট:
<li><span class="key-term">বাংলাদেশের জাতীয় ফুল</span>- <span class="highlight">শাপলা</span></li>

ভুল অপশনগুলো ফেলে দিবে, শুধু প্রশ্ন ও সঠিক উত্তরকে "টার্ম- উত্তর" আকারে বুলেট বানাবে, যাতে পড়তে সহজ হয়।

=== অন্যান্য নিয়ম ===
5. কোনো প্যারাগ্রাফ হুবহু কপি না করে, ছোট ছোট "টার্ম- উত্তর" বুলেটে ভাঙবে।
6. তুলনামূলক/শ্রেণীবদ্ধ তথ্য অবশ্যই টেবিলে দিবে।
7. ধারাবাহিক প্রক্রিয়া/স্তরবিন্যাস অবশ্যই flow-diagram এ দিবে।
8. সকল সংখ্যা/তারিখ/নাম অবশ্যই <span class="highlight"> দিয়ে হাইলাইট করবে।
9. প্রতিটা টপিক <div class="topic-section"> দিয়ে মোড়ানো থাকবে।
10. টপিকগুলোর মাঝে কোনো page-break বা ফাঁকা জায়গা দিবে না।
11. আউটপুট শুধু raw HTML fragment, অন্য কিছু নয়।
{custom_instruction_block}
{chunk_info}

নিচের কন্টেন্টের প্রতিটা তথ্য বিস্তারিতভাবে, কিছু বাদ না দিয়ে উপরের নিয়ম (এবং থাকলে, ব্যবহারকারীর বিশেষ নির্দেশনা) মেনে নোট বানাও:

{content_text}
"""

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt)
            html_fragment, finish_reason = _safe_extract_text(response)

            if html_fragment.startswith("```"):
                html_fragment = html_fragment.strip("`")
                html_fragment = html_fragment.replace("html", "", 1).strip()

            if not html_fragment:
                raise RuntimeError("খালি রেসপন্স এসেছে।")

            was_truncated = (finish_reason == 2)  # 2 = MAX_TOKENS
            return html_fragment, was_truncated

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            else:
                raise RuntimeError(f"{max_retries} বার চেষ্টা করেও ব্যর্থ হয়েছে। শেষ error: {last_error}")


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