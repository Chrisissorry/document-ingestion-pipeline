"""Generate fictional sample PDFs into samples/. Run once after cloning.

    docker compose run --rm ingest python scripts/make_samples.py
    docker compose run --rm ingest python scripts/make_samples.py --count 20 --seed 42

Core-font (Helvetica) output is latin-1, which covers German umlauts. The Euro
sign is not in latin-1, so amounts use "EUR".

Scan variants (_scan_) are image-only: text is rendered onto a PIL Image and
embedded as a PNG. pdfplumber returns "" for these, exercising the Vision route.
"""

from __future__ import annotations

import argparse
import io
import json
import random
from pathlib import Path
from typing import TypedDict

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PIL import Image, ImageDraw, ImageFont

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
EXPECTED = SAMPLES / "expected"


class LineItem(TypedDict):
    description: str
    amount: float


# ---------------------------------------------------------------------------
# Randomization pools
# ---------------------------------------------------------------------------

EN_VENDORS = [
    "ACME Supplies Ltd.",
    "Initech Solutions GmbH",
    "Globex Services Ltd.",
    "Umbrella Consulting Inc.",
    "Dunder Mifflin Corp.",
    "Prestige Worldwide Ltd.",
    "Sterling Cooper Partners",
    "Veridian Dynamics Ltd.",
    "Wolfram & Hart Legal",
    "Soylent Corp. Inc.",
    "Initrode Software Ltd.",
    "Cyberdyne Systems Corp.",
    "Rekall Inc.",
    "Weyland-Yutani Ltd.",
    "Spacely Sprockets Inc.",
]

DE_VENDORS = [
    "Mueller Buerobedarf GmbH",
    "Schneider Handels AG",
    "Fischer Logistik GmbH",
    "Weber Maschinenbau GmbH",
    "Meyer Consulting GmbH",
    "Schmidt Verwaltungs AG",
    "Lehmann Technik GmbH",
    "Koch Software GmbH",
    "Becker Dienstleistungen AG",
    "Hoffmann Bueroservice GmbH",
    "Schaefer Systeme GmbH",
    "Richter Immobilien AG",
    "Wolf Beratungs GmbH",
    "Braun Handel GmbH",
    "Zimmermann Logistik AG",
]

EN_CUSTOMERS = [
    "Globex Corporation",
    "Initech LLC",
    "Veridian Dynamics",
    "Prestige Worldwide",
    "Sterling Cooper",
    "Massive Dynamic Inc.",
    "Umbrella Corporation",
    "Rekall Industries",
    "Spacely Industries",
    "Cogswell Cogs Inc.",
]

DE_CUSTOMERS = [
    "Schmidt Handels AG",
    "Bauer GmbH",
    "Richter AG",
    "Zimmermann KG",
    "Braun Beteiligungen AG",
]

CURRENCIES = ["EUR", "USD", "GBP"]

EN_SERVICE_ITEMS: list[tuple[str, float]] = [
    ("Consulting services", 900.0),
    ("Software development", 1200.0),
    ("Project management", 750.0),
    ("Technical support", 450.0),
    ("Training sessions", 600.0),
    ("Audit and compliance", 1100.0),
    ("Data migration", 850.0),
    ("Security assessment", 980.0),
    ("Travel expenses", 119.0),
    ("Hosting fees", 299.0),
    ("Licensing fees", 500.0),
    ("Documentation", 350.0),
]

DE_SERVICE_ITEMS: list[tuple[str, float]] = [
    ("Buerostuehle (3 Stueck)", 447.0),
    ("Schreibtisch", 289.0),
    ("Druckerpatronen", 89.0),
    ("Aktenvernichter", 199.0),
    ("Laptoptasche", 79.0),
    ("Monitorstaender", 149.0),
    ("Tastatur und Maus", 119.0),
    ("Whiteboard", 229.0),
    ("Stehpulzaufsatz", 349.0),
    ("Rollcontainer", 189.0),
]

CAFE_NAMES = [
    "Cafe Central",
    "Kaffeehaus Mitte",
    "Bistro am Markt",
    "Baeckerei Schneider",
    "Cafe Latte",
    "The Coffee Corner",
    "Espresso Bar",
    "Cafe Morgen",
]

CAFE_ITEMS: list[tuple[str, float]] = [
    ("Cappuccino", 3.80),
    ("Latte Macchiato", 4.20),
    ("Espresso", 2.50),
    ("Americano", 3.20),
    ("Croissant", 2.40),
    ("Muffin", 2.80),
    ("Sandwich", 5.50),
    ("Kuchen", 3.50),
    ("Mineralwasser", 2.00),
    ("Orangensaft", 3.80),
]

CONTRACT_PARTIES = [
    "Initech LLC",
    "Globex Corporation",
    "Prestige Worldwide Ltd.",
    "Sterling Cooper Partners",
    "Umbrella Consulting Inc.",
    "Veridian Dynamics Ltd.",
    "Wolfram & Hart Legal",
    "Massive Dynamic Inc.",
    "Cogswell Cogs Inc.",
    "Spacely Industries",
]

CONTRACT_TERMS = ["6 months", "12 months", "24 months", "36 months"]

PERSON_NAMES = [
    ("Jane", "Doe"),
    ("John", "Smith"),
    ("Maria", "Gonzalez"),
    ("Thomas", "Muster"),
    ("Sophie", "Dupont"),
    ("Alex", "Chen"),
    ("Lena", "Schulz"),
    ("Mark", "Johnson"),
    ("Anna", "Mueller"),
    ("Chris", "Taylor"),
]

LETTER_SUBJECTS = [
    "your inquiry regarding our services",
    "the upcoming project kickoff",
    "the contract renewal",
    "your feedback on our proposal",
    "the scheduled service review",
    "the partnership agreement",
    "your order from last month",
    "the support ticket resolution",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_date(rng: random.Random, year: int = 2026) -> str:
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def _vary_amount(rng: random.Random, base: float) -> float:
    factor = rng.uniform(0.8, 1.2)
    return round(base * factor, 2)


def _write_pdf(name: str, lines: list[str]) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 8, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(SAMPLES / name))
    print(f"wrote {name}")


def _write_scan(name: str, lines: list[str]) -> None:
    width, height = 1240, 1754  # A4 at 150 dpi
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", size=28)
    except OSError:
        font = ImageFont.load_default()
    y = 80
    for line in lines:
        draw.text((80, y), line, fill=(0, 0, 0), font=font)
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    pdf = FPDF()
    pdf.add_page()
    pdf.image(buf, x=0, y=0, w=210)  # fill A4 width; no cell() calls = no text layer
    pdf.output(str(SAMPLES / name))
    print(f"wrote {name}")


def _write_golden(name: str, golden: dict) -> None:
    path = EXPECTED / name
    path.write_text(json.dumps(golden, indent=2))
    print(f"wrote expected/{name}")


# ---------------------------------------------------------------------------
# Document factories — each returns (pdf_filename, lines, golden_dict)
# ---------------------------------------------------------------------------


def _make_invoice(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    vendor = rng.choice(EN_VENDORS)
    customer = rng.choice(EN_CUSTOMERS)
    date = _random_date(rng)
    currency = rng.choice(CURRENCIES)
    inv_num = f"INV-{date[:4]}-{n:04d}"
    items = rng.sample(EN_SERVICE_ITEMS, k=rng.randint(1, 3))
    line_items: list[LineItem] = [
        {"description": desc, "amount": _vary_amount(rng, base)} for desc, base in items
    ]
    subtotal = round(sum(i["amount"] for i in line_items), 2)
    vat = round(subtotal * 0.20, 2)
    total = round(subtotal + vat, 2)

    lines = [
        vendor,
        "123 Market Street, London EC1A 1BB",
        "",
        "INVOICE",
        "",
        f"Invoice Number: {inv_num}",
        f"Date: {date}",
        f"Bill To: {customer}",
        "",
        *[f"{i['description']:<25} {i['amount']:.2f}" for i in line_items],
        "",
        f"Subtotal: {subtotal:.2f}",
        f"VAT (20%): {vat:.2f}",
        f"Total: {total:.2f} {currency}",
    ]
    filename = f"invoice_{n:04d}.pdf"
    golden = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "invoice",
        "confidence": 0.95,
        "fields": {
            "doc_type": "invoice",
            "invoice_number": inv_num,
            "date": date,
            "vendor": vendor,
            "currency": currency,
            "total": total,
            "line_items": line_items,
        },
    }
    return filename, lines, golden


def _make_invoice_de(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    vendor = rng.choice(DE_VENDORS)
    customer = rng.choice(DE_CUSTOMERS)
    date = _random_date(rng)
    inv_num = f"RE-{date[:4]}-{n:04d}"
    items = rng.sample(DE_SERVICE_ITEMS, k=rng.randint(1, 3))
    line_items: list[LineItem] = [
        {"description": desc, "amount": _vary_amount(rng, base)} for desc, base in items
    ]
    subtotal = round(sum(i["amount"] for i in line_items), 2)
    vat = round(subtotal * 0.19, 2)
    total = round(subtotal + vat, 2)

    lines = [
        vendor,
        "Hauptstrasse 5, 10115 Berlin",
        "",
        "RECHNUNG",
        "",
        f"Rechnungsnummer: {inv_num}",
        f"Datum: {date}",
        f"Kunde: {customer}",
        "",
        *[f"{i['description']:<30} {i['amount']:.2f}" for i in line_items],
        "",
        f"Zwischensumme: {subtotal:.2f}",
        f"MwSt (19%): {vat:.2f}",
        f"Gesamtbetrag: {total:.2f} EUR",
    ]
    filename = f"invoice_de_{n:04d}.pdf"
    golden = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "invoice",
        "confidence": 0.95,
        "fields": {
            "doc_type": "invoice",
            "invoice_number": inv_num,
            "date": date,
            "vendor": vendor,
            "currency": "EUR",
            "total": total,
            "line_items": line_items,
        },
    }
    return filename, lines, golden


def _make_contract(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    parties = rng.sample(CONTRACT_PARTIES, k=2)
    date = _random_date(rng)
    term = rng.choice(CONTRACT_TERMS)

    lines = [
        "SERVICE AGREEMENT",
        "",
        "This agreement is entered into between:",
        f"Party A: {parties[0]}",
        f"Party B: {parties[1]}",
        "",
        f"Effective Date: {date}",
        f"Term: {term}, auto-renewing",
        "",
        "1. Scope of services ...",
        "2. Fees and payment ...",
        "3. Termination ...",
    ]
    filename = f"contract_{n:04d}.pdf"
    golden = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "contract",
        "confidence": 0.95,
        "fields": {
            "doc_type": "contract",
            "parties": parties,
            "effective_date": date,
            "term": term,
        },
    }
    return filename, lines, golden


def _make_receipt(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    cafe = rng.choice(CAFE_NAMES)
    date = _random_date(rng)
    hour = rng.randint(8, 18)
    minute = rng.randint(0, 59)
    items = rng.sample(CAFE_ITEMS, k=rng.randint(1, 3))
    line_items: list[LineItem] = [
        {"description": desc, "amount": _vary_amount(rng, base)} for desc, base in items
    ]
    total = round(sum(i["amount"] for i in line_items), 2)

    lines = [
        cafe,
        "Marktplatz 2, 10178 Berlin",
        "",
        "QUITTUNG / RECEIPT",
        f"Datum: {date}  {hour:02d}:{minute:02d}",
        "",
        *[f"{i['description']:<20} {i['amount']:.2f}" for i in line_items],
        "",
        f"Summe: {total:.2f} EUR",
        "Zahlart: Karte",
    ]
    filename = f"receipt_{n:04d}.pdf"
    golden = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "generic",
        "confidence": 0.95,
        "fields": {
            "doc_type": "generic",
            "title": f"Receipt — {cafe}",
            "summary": f"Receipt dated {date}, total {total:.2f} EUR.",
        },
    }
    return filename, lines, golden


def _make_letter(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    sender_first, sender_last = rng.choice(PERSON_NAMES)
    recipient_first, recipient_last = rng.choice(PERSON_NAMES)
    company = rng.choice(EN_VENDORS)
    date = _random_date(rng)
    subject = rng.choice(LETTER_SUBJECTS)

    lines = [
        company,
        "42 Industrial Way, Springfield",
        "",
        date,
        "",
        f"Dear {recipient_first} {recipient_last},",
        "",
        f"Thank you for {subject}.",
        "We are pleased to confirm the meeting on the agreed date.",
        "",
        "Kind regards,",
        f"{sender_first} {sender_last}",
        "Account Manager",
    ]
    filename = f"letter_{n:04d}.pdf"
    golden = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "generic",
        "confidence": 0.95,
        "fields": {
            "doc_type": "generic",
            "title": f"Letter from {company}",
            "summary": f"Letter dated {date} regarding {subject}.",
        },
    }
    return filename, lines, golden


def _make_invoice_scan(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    _, lines, golden = _make_invoice(n, rng)
    filename = f"invoice_scan_{n:04d}.pdf"
    golden = {**golden, "source": f"samples/{filename}", "tier": "vision"}
    return filename, lines, golden


def _make_receipt_scan(n: int, rng: random.Random) -> tuple[str, list[str], dict]:
    _, lines, golden = _make_receipt(n, rng)
    filename = f"receipt_scan_{n:04d}.pdf"
    golden = {**golden, "source": f"samples/{filename}", "tier": "vision"}
    return filename, lines, golden


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _write_pages(name: str, pages: list[list[str]]) -> None:
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for page in pages:
        pdf.add_page()
        for line in page:
            pdf.cell(0, 8, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(SAMPLES / name))
    print(f"wrote {name}")


def _make_invoice_missing_fields(_n: int, _rng: random.Random) -> tuple[str, list[str], dict]:
    filename = "sample_invoice_missing_fields.pdf"
    lines = [
        "INVOICE",
        "",
        "Bill To: Riverdale Partners GmbH",
        "Attn: Procurement Department",
        "",
        "Consulting services rendered during Q2.",
        "",
        "Please arrange payment at your earliest convenience.",
        "Bank details available on request.",
    ]
    golden: dict = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "invoice",
        "confidence": 0.3,
        "fields": {
            "doc_type": "invoice",
            "invoice_number": None,
            "date": None,
            "vendor": None,
            "currency": None,
            "total": None,
            "line_items": [],
        },
    }
    return filename, lines, golden


def _make_unclassifiable(_n: int, _rng: random.Random) -> tuple[str, list[str], dict]:
    filename = "sample_unclassifiable.pdf"
    lines = [
        "INTERNAL MEMO",
        "",
        "Ref: Q3 Planning Cycle",
        "Distribution: All Department Heads",
        "Priority: Normal",
        "",
        "Please review the attached materials before Friday.",
        "Action items will be tracked separately.",
        "",
        "- Asset utilisation targets remain under review.",
        "- No decisions have been finalised at this stage.",
        "",
        "This memo does not constitute a legal agreement.",
    ]
    golden: dict = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "generic",
        "confidence": 0.6,
        "fields": {
            "doc_type": "generic",
            "title": "Internal Memo — Q3 Planning",
            "summary": "Internal memo about Q3 planning with action items for department heads.",
        },
    }
    return filename, lines, golden


def _make_multipage_contract(_n: int, _rng: random.Random) -> tuple[str, list[list[str]], dict]:
    filename = "sample_multipage.pdf"
    pages = [
        [
            "SERVICE AGREEMENT  (page 1 of 2)",
            "",
            "This agreement is entered into between:",
            "Party A: Pinnacle Consulting UG",
            "Party B: Horizon Retail GmbH",
            "",
            "Effective Date: 2026-07-01",
            "Term: 24 months",
            "",
            "1. Scope of Services",
            "   Pinnacle Consulting UG shall provide strategic advisory",
            "   services as detailed in Schedule A, attached hereto.",
            "",
            "2. Fees",
            "   Monthly retainer: 4500.00 EUR, invoiced on the 1st.",
            "   Expenses reimbursed at cost with prior written approval.",
        ],
        [
            "SERVICE AGREEMENT  (page 2 of 2)",
            "",
            "3. Confidentiality",
            "   Each party shall keep confidential all proprietary",
            "   information received from the other party.",
            "",
            "4. Termination",
            "   Either party may terminate with 30 days written notice.",
            "   Fees accrued to the termination date remain payable.",
            "",
            "5. Governing Law",
            "   This agreement is governed by the laws of Germany.",
            "",
            "Signed:",
            "",
            "Party A: ____________________  Date: __________",
            "Party B: ____________________  Date: __________",
        ],
    ]
    golden: dict = {
        "source": f"samples/{filename}",
        "tier": "text",
        "doc_type": "contract",
        "confidence": 0.9,
        "fields": {
            "doc_type": "contract",
            "parties": ["Pinnacle Consulting UG", "Horizon Retail GmbH"],
            "effective_date": "2026-07-01",
            "term": "24 months",
        },
    }
    return filename, pages, golden


FACTORIES_TEXT = [_make_invoice, _make_invoice_de, _make_contract, _make_receipt, _make_letter]
FACTORIES_SCAN = [_make_invoice_scan, _make_receipt_scan]
FACTORIES_SPECIAL = [_make_invoice_missing_fields, _make_unclassifiable]
FACTORIES_SPECIAL_MULTIPAGE = [_make_multipage_contract]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate fictional sample PDFs with golden JSONs."
    )
    parser.add_argument(
        "--count", type=int, default=1, help="Variants per document type (default: 1)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()

    SAMPLES.mkdir(exist_ok=True)
    EXPECTED.mkdir(exist_ok=True)

    rng = random.Random(args.seed)

    for n in range(1, args.count + 1):
        for factory in FACTORIES_TEXT:
            filename, lines, golden = factory(n, rng)
            _write_pdf(filename, lines)
            _write_golden(filename.replace(".pdf", ".json"), golden)

        for factory in FACTORIES_SCAN:
            filename, lines, golden = factory(n, rng)
            _write_scan(filename, lines)
            _write_golden(filename.replace(".pdf", ".json"), golden)

    for factory in FACTORIES_SPECIAL:
        filename, lines, golden = factory(0, rng)
        _write_pdf(filename, lines)
        _write_golden(filename.replace(".pdf", ".json"), golden)

    for factory in FACTORIES_SPECIAL_MULTIPAGE:
        filename, pages, golden = factory(0, rng)
        _write_pages(filename, pages)
        _write_golden(filename.replace(".pdf", ".json"), golden)


if __name__ == "__main__":
    main()
