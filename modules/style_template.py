from pathlib import Path


def _get_font_face_css():
    base_dir = Path(__file__).resolve().parent.parent
    fonts_dir = base_dir / "fonts"
    regular = (fonts_dir / "NotoSansBengali-Regular.ttf").as_uri()
    bold = (fonts_dir / "NotoSansBengali-Bold.ttf").as_uri()

    return f"""
    @font-face {{
        font-family: 'NotoBengali';
        src: url('{regular}');
        font-weight: normal;
    }}
    @font-face {{
        font-family: 'NotoBengali';
        src: url('{bold}');
        font-weight: bold;
    }}
    """


def get_full_css():
    font_faces = _get_font_face_css()

    return f"""
    {font_faces}

    * {{
        font-family: 'NotoBengali', sans-serif;
        box-sizing: border-box;
    }}

    body {{
        font-size: 11.5pt;
        line-height: 1.5;
        color: #1a1a1a;
    }}

    @page {{
        size: A4;
        margin: 2.3cm 1.3cm 2cm 1.3cm;

        @top-center {{ content: element(pageHeader); }}
        @bottom-center {{ content: element(pageFooter); }}
    }}

    #page-header {{
        position: running(pageHeader);
        width: 100%;
        text-align: center;
        font-size: 9pt;
        font-weight: bold;
        color: #0b2545;
        border-bottom: 1.5px solid #0b2545;
        padding-bottom: 4px;
    }}

    #page-footer {{
        position: running(pageFooter);
        width: 100%;
        text-align: center;
        font-size: 8pt;
        color: #555;
        border-top: 1px solid #ccc;
        padding-top: 3px;
    }}

    .cover-page {{
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }}
    .cover-title {{ font-size: 28pt; font-weight: bold; color: #0b2545; margin-bottom: 12px; }}
    .cover-sub {{ font-size: 14pt; color: #333; }}

    .page-break {{ break-before: page; }}

    /* === মূল ফিক্স: টপিক একটার পর একটা, জায়গা নষ্ট হবে না === */
    .topic-section {{
        break-inside: avoid;
        page-break-inside: avoid;
        margin-bottom: 16px;
    }}

    .topic-title {{
        background-color: #0b2545;
        color: #ffffff;
        font-weight: bold;
        font-size: 13pt;
        text-align: center;
        padding: 6px 10px;
        margin-bottom: 8px;
        border-radius: 3px;
        break-after: avoid-page;
    }}

    .sub-heading {{
        background-color: #dceaf7;
        border-left: 4px solid #0b2545;
        font-weight: bold;
        font-size: 11.5pt;
        padding: 4px 8px;
        margin: 8px 0 6px 0;
        break-after: avoid-page;
    }}

    .fact-list {{ list-style: none; margin: 0 0 8px 0; padding: 0; }}
    .fact-list li {{ position: relative; padding-left: 16px; margin-bottom: 4px; }}
    .fact-list li::before {{
        content: "▪"; position: absolute; left: 0;
        color: #0b2545; font-weight: bold;
    }}

    .sub-point {{ margin-left: 22px; font-size: 10.5pt; color: #333; margin-bottom: 3px; }}
    .sub-point::before {{ content: "↳ "; color: #0b2545; }}

    .key-term {{ font-weight: bold; color: #0b2545; }}
    .highlight {{ font-weight: bold; color: #c0392b; }}

    .info-table {{
        width: 100%; border-collapse: collapse;
        margin: 8px 0 12px 0; font-size: 10.5pt;
        break-inside: avoid;
    }}
    .info-table th {{
        background-color: #0b2545; color: #fff;
        padding: 5px 7px; text-align: left; border: 1px solid #0b2545;
    }}
    .info-table td {{ padding: 5px 7px; border: 1px solid #ccc; }}
    .info-table tr:nth-child(even) td {{ background-color: #f2f6fa; }}

    .flow-diagram {{ margin: 10px 0; break-inside: avoid; }}
    .flow-box {{
        border: 1.5px solid #0b2545; background-color: #eef5fc;
        padding: 6px 10px; margin: 0 auto; text-align: center;
        font-weight: bold; font-size: 10.5pt; width: fit-content; border-radius: 4px;
    }}
    .flow-arrow {{ text-align: center; font-size: 14pt; color: #0b2545; margin: 2px 0; }}
    """