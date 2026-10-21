import requests
from bs4 import BeautifulSoup


def extract_text_from_url(url):
    """এক URL থেকে মূল টেক্সট কন্টেন্ট বের করে আনে"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        return {"success": True, "url": url, "content": clean_text}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


def extract_text_from_multiple_urls(url_text_block):
    """একাধিক URL (নতুন লাইনে আলাদা) থেকে টেক্সট টেনে এক সাথে জোড়া দেয়"""
    urls = [u.strip() for u in url_text_block.splitlines() if u.strip()]
    combined = ""
    errors = []

    for url in urls:
        result = extract_text_from_url(url)
        if result["success"]:
            combined += f"\n\n=== SOURCE: {url} ===\n\n{result['content']}"
        else:
            errors.append(f"{url} -> {result['error']}")

    return combined, errors