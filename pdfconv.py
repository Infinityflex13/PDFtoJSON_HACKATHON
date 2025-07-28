import fitz  # PyMuPDF
import os, sys, json, re
from collections import Counter

def clean(text: str) -> str:
    text = re.sub(r'\s+\d+\s*$', '', text)
    text = re.sub(r'[:\u2013\u2014\-\.]+$', '', text)
    return re.sub(r'\s{2,}', ' ', text).strip()

def is_paragraph(txt: str) -> bool:
    return txt.count(' ') > 10 or len(txt) > 120

def is_toc_line(txt: str) -> bool:
    return re.search(r'\d+\s+\d+\.\d+', txt) or re.search(r'\d+\s+\d+$', txt)

def is_form_field(txt: str) -> bool:
    return (re.match(r'^\d+\.\s*$', txt) or
            re.match(r'^\d+\.\s+[A-Z][a-z\s]+$', txt) or
            txt.lower() in ['name', 'designation', 'date', 'pay', 'service'])

def extract_pdf_outline(pdf_path: str) -> dict:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return {"title": "", "headings": []}

    outline = {"title": "", "headings": []}
    blocks = []
    for page_no, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            if "lines" not in b:
                continue
            txt, max_size, y_sum, n = "", 0, 0.0, 0
            bold = False
            for line in b["lines"]:
                for sp in line["spans"]:
                    t = sp["text"].strip()
                    if not t:
                        continue
                    txt += t + " "
                    max_size = max(max_size, sp["size"])
                    y_sum += sp["bbox"][1]
                    n += 1
                    bold |= bool(sp["flags"] & 16)
            if txt.strip():
                blocks.append({
                    "text": txt.strip(),
                    "size": round(max_size, 1),
                    "page": page_no,
                    "y": y_sum / n,
                    "bold": bold
                })

    first = [b for b in blocks if b["page"] == 1 and b["y"] < 250]
    if first:
        first.sort(key=lambda x: x["y"])
        has_numbered = any(re.match(r'^\d+\.\s+', b["text"]) for b in first[:5])
        if has_numbered:
            for b in first:
                if (len(b["text"]) > 10 and not is_form_field(b["text"]) and not re.match(r'^\d+\.\s+', b["text"])):
                    outline["title"] = clean(b["text"]) + "  "
                    break
        else:
            top_size = max(b["size"] for b in first)
            title_parts = [b["text"] for b in first if b["size"] >= top_size * 0.8 and not is_paragraph(b["text"])]
            if title_parts:
                outline["title"] = clean(" ".join(title_parts))
            else:
                outline["title"] = clean(first[0]["text"])

    if not outline["title"]:
        outline["title"] = os.path.splitext(os.path.basename(pdf_path))[0]

    stats_blocks = [b for b in blocks if not (b["page"] == 1 and b["y"] < 250)]
    if not stats_blocks:
        doc.close()
        return outline

    body_size = Counter(b["size"] for b in stats_blocks).most_common(1)[0][0]
    heading_sizes = sorted({s for s in Counter(b["size"] for b in stats_blocks) if s > body_size * 1.15}, reverse=True)[:3]
    size_rank = {s: i + 1 for i, s in enumerate(heading_sizes)}

    RX_H1 = re.compile(r'^\d+\.\s+[A-Z]')
    RX_H2 = re.compile(r'^\d+\.\d+\s+[A-Z]')
    RX_H3 = re.compile(r'^\d+\.\d+\.\d+\s+[A-Z]')
    KNOWN = {"revision history", "table of contents", "acknowledgements", "references"}

    page_nums = Counter(b["page"] for b in blocks if RX_H1.match(b["text"]) or RX_H2.match(b["text"]))
    toc_pages = {p for p, count in page_nums.items() if count > 5 and p < 10}

    seen = set()
    for b in blocks:
        page, txt_raw = b["page"], b["text"]
        txt = clean(txt_raw)
        low = txt.lower()

        if not txt or low in seen:
            continue
        if is_paragraph(txt):
            continue
        if is_toc_line(txt):
            continue
        if page == 1 and low in outline["title"].lower():
            continue
        if low.startswith("international software testing"):
            continue
        if page in toc_pages and "table of contents" not in low:
            continue

        lvl = None
        if low in KNOWN and len(txt.split()) <= 4:
            lvl = "H1"
        elif RX_H3.match(txt):
            lvl = "H3"
        elif RX_H2.match(txt):
            lvl = "H2"
        elif RX_H1.match(txt):
            lvl = "H1"
        elif b["size"] in heading_sizes and txt[0].isupper():
            lvl = f"H{size_rank[b['size']]}"

        if lvl:
            outline["headings"].append({"level": lvl, "text": txt, "page": page - 1})
            seen.add(low)

    outline["headings"].sort(key=lambda h: (h["page"]))
    doc.close()
    return outline

# 🧠 New simplified I/O loop (no CLI args)
if __name__ == "__main__":
    input_dir = "input"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in 'input/'")
        sys.exit(1)

    for pdf_file in pdf_files:
        path = os.path.join(input_dir, pdf_file)
        try:
            res = extract_pdf_outline(path)
            out_path = os.path.join(output_dir, os.path.splitext(pdf_file)[0] + "_outline.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
            print("✔ Saved outline to", out_path)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")