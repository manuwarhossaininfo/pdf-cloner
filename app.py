import streamlit as st
import tempfile
import os
import time

from modules.api_tester import test_api_connection, list_available_models
from modules.content_extractor import extract_all_content, chunk_plain_text
from modules.input_handler import extract_text_from_multiple_urls
from modules.pdf_builder import generate_notes_html, build_final_html, convert_html_to_pdf

st.set_page_config(page_title="Exam-Style Note Generator", page_icon="📘", layout="wide")
st.title("📘 Exam-Style Note Generator")

# ---------------- Sidebar ----------------
st.sidebar.header("⚙️ API Settings")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

model_options = [
    "gemini-3.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
    "Custom"
]
model_choice = st.sidebar.selectbox("Model", model_options)
model_name = st.sidebar.text_input("Custom model name") if model_choice == "Custom" else model_choice

if "api_status" not in st.session_state:
    st.session_state.api_status = None

if st.sidebar.button("🔌 Test API Connection"):
    if not api_key:
        st.sidebar.error("আগে API Key দাও।")
    else:
        result = test_api_connection(api_key, model_name)
        st.session_state.api_status = result
        (st.sidebar.success if result["success"] else st.sidebar.error)(result["message"])

if st.sidebar.button("📋 Show Available Models"):
    if not api_key:
        st.sidebar.error("আগে API Key দাও।")
    else:
        st.sidebar.write(list_available_models(api_key))

if st.session_state.api_status and st.session_state.api_status["success"]:
    st.sidebar.markdown("✅ **API Connected**")

st.markdown("---")

# ---------------- Branding ----------------
st.subheader("🏷️ Branding")
col1, col2 = st.columns(2)
with col1:
    brand_name = st.text_input("Brand/Course Name", value="My Exam Notes")
with col2:
    author_name = st.text_input("Author Name", value="Your Name")

st.markdown("---")

# ---------------- Content Sources ----------------
st.subheader("📥 Content Source (যেকোনো একটা বা একাধিক দিতে পারো)")

uploaded_pdf = st.file_uploader("📄 Content PDF (optional, max 300 pages)", type=["pdf"])
pasted_text = st.text_area("✍️ অথবা সরাসরি টেক্সট পেস্ট করো (optional)", height=180)
url_block = st.text_area(
    "🔗 অথবা URL দাও (একাধিক হলে প্রতিটা নতুন লাইনে, optional)",
    height=100,
    placeholder="https://example.com/article-1\nhttps://example.com/article-2"
)

with st.expander("⚙️ Advanced Options"):
    chunk_size_pages = st.slider("Chunk size (approx. pages worth per chunk)", 5, 40, 20)
    delay = st.slider("Delay between API calls (seconds)", 1, 10, 3)

st.markdown("---")

# ---------------- Generate ----------------
if st.button("🎯 Generate Exam-Style Notes PDF"):

    if not api_key:
        st.error("❌ আগে API Key দাও।")
        st.stop()

    if not (st.session_state.api_status and st.session_state.api_status["success"]):
        st.error("❌ আগে 'Test API Connection' দিয়ে চেক করো।")
        st.stop()

    if not uploaded_pdf and not pasted_text.strip() and not url_block.strip():
        st.error("❌ PDF, টেক্সট, অথবা URL — অন্তত একটা দিতে হবে।")
        st.stop()

    combined_text = ""

    if uploaded_pdf:
        with st.spinner("PDF থেকে কন্টেন্ট বের করা হচ্ছে..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_pdf.read())
                tmp_path = tmp.name
            combined_text += f"\n\n=== SOURCE: PDF ({uploaded_pdf.name}) ===\n\n{extract_all_content(tmp_path)}"
            os.unlink(tmp_path)

    if pasted_text.strip():
        combined_text += f"\n\n=== SOURCE: Pasted Text ===\n\n{pasted_text.strip()}"

    if url_block.strip():
        with st.spinner("URL থেকে কন্টেন্ট টানা হচ্ছে..."):
            url_text, url_errors = extract_text_from_multiple_urls(url_block)
            combined_text += url_text
            for err in url_errors:
                st.warning(f"⚠️ URL fetch সমস্যা: {err}")

    if not combined_text.strip():
        st.error("❌ কোনো কন্টেন্ট পাওয়া যায়নি।")
        st.stop()

    words_per_chunk = chunk_size_pages * 450
    chunks = chunk_plain_text(combined_text, words_per_chunk=words_per_chunk)

    st.info(f"মোট {len(chunks)}টা chunk-এ ভাগ করা হয়েছে। প্রসেসিং শুরু হচ্ছে...")

    progress_bar = st.progress(0)
    status_text = st.empty()
    body_fragments = []
    failed_chunks = []

    for idx, chunk in enumerate(chunks):
        status_text.text(f"Processing chunk {idx+1}/{len(chunks)}...")
        try:
            chunk_info = f"(এটি সম্পূর্ণ কন্টেন্টের {idx+1} নম্বর অংশ, মোট {len(chunks)} অংশের মধ্যে)"
            fragment = generate_notes_html(api_key, model_name, chunk["content"], chunk_info)
            body_fragments.append(fragment)
        except Exception as e:
            failed_chunks.append(idx + 1)
            st.warning(f"⚠️ Chunk {idx+1} এ সমস্যা: {e}")

        progress_bar.progress((idx + 1) / len(chunks))
        time.sleep(delay)

    if not body_fragments:
        st.error("❌ কোনো কন্টেন্ট জেনারেট হয়নি।")
        st.stop()

    status_text.text("PDF তৈরি করা হচ্ছে...")
    final_html = build_final_html(brand_name, author_name, body_fragments)
    output_path = os.path.join(tempfile.gettempdir(), "exam_notes_output.pdf")

    try:
        convert_html_to_pdf(final_html, output_path)
        st.success("✅ PDF সফলভাবে তৈরি হয়েছে!")
        with open(output_path, "rb") as f:
            st.download_button("⬇️ Download PDF", data=f,
                                file_name=f"{brand_name.replace(' ', '_')}_notes.pdf",
                                mime="application/pdf")
    except Exception as e:
        st.error(f"❌ PDF বানাতে সমস্যা: {e}")
        st.download_button("🐞 Debug HTML ডাউনলোড", data=final_html,
                            file_name="debug_output.html", mime="text/html")

    if failed_chunks:
        st.warning(f"⚠️ এই chunk গুলো fail হয়েছে: {failed_chunks}")