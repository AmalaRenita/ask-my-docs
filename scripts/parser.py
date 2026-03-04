import json
from pathlib import Path
from lxml import etree

# Input and output folders
SAMPLED_DIR = Path("data/sampled")
PARSED_DIR = Path("data/parsed")
PARSED_DIR.mkdir(parents=True, exist_ok=True)

def extract_text(element):
    """Get all text from an element including nested tags"""
    if element is None:
        return ""
    return " ".join(element.itertext()).strip()

def parse_xml_file(filepath: Path) -> dict | None:
    """Parse a single PubMed XML file into a clean dictionary"""
    try:
        tree = etree.parse(filepath)
        root = tree.getroot()

        # ── Extract PMC ID ──────────────────────────────
        pmc_id = ""
        for article_id in root.findall(".//article-id"):
            if article_id.get("pub-id-type") == "pmc":
                pmc_id = article_id.text or ""

        # ── Extract DOI ─────────────────────────────────
        doi = ""
        for article_id in root.findall(".//article-id"):
            if article_id.get("pub-id-type") == "doi":
                doi = article_id.text or ""

        # ── Extract Title ────────────────────────────────
        title_elem = root.find(".//article-title")
        title = extract_text(title_elem)

        # ── Extract Journal Name ─────────────────────────
        journal_elem = root.find(".//journal-title")
        journal = extract_text(journal_elem)

        # ── Extract Publication Date ─────────────────────
        year = ""
        month = ""
        pub_date = root.find(".//pub-date[@pub-type='ppub']")
        if pub_date is None:
            pub_date = root.find(".//pub-date")
        if pub_date is not None:
            year_elem = pub_date.find("year")
            month_elem = pub_date.find("month")
            year = year_elem.text if year_elem is not None else ""
            month = month_elem.text if month_elem is not None else ""

        # ── Extract Body Text ────────────────────────────
        body_paragraphs = []
        body = root.find(".//body")
        if body is not None:
            for p in body.findall(".//p"):
                text = extract_text(p)
                if text:
                    body_paragraphs.append(text)
        body_text = "\n\n".join(body_paragraphs)

        # ── Skip if no useful content ────────────────────
        if not title and not body_text:
            return None

        return {
            "pmc_id": pmc_id,
            "doi": doi,
            "title": title,
            "journal": journal,
            "year": year,
            "month": month,
            "body_text": body_text,
            "source_file": filepath.name
        }

    except Exception as e:
        print(f"Error parsing {filepath.name}: {e}")
        return None

def main():
    xml_files = list(SAMPLED_DIR.glob("*.xml"))
    print(f"Found {len(xml_files)} XML files to parse")

    success = 0
    failed = 0

    for i, filepath in enumerate(xml_files):
        # Show progress every 100 files
        if i % 100 == 0:
            print(f"Processing {i}/{len(xml_files)}...")

        result = parse_xml_file(filepath)

        if result:
            # Save as JSON with same name but .json extension
            output_path = PARSED_DIR / filepath.stem
            output_path = output_path.with_suffix(".json")
            output_path.write_text(json.dumps(result, indent=2))
            success += 1
        else:
            failed += 1

    print(f"\nDone!")
    print(f"Successfully parsed: {success}")
    print(f"Failed/skipped:      {failed}")

if __name__ == "__main__":
    main()