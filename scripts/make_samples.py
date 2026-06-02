"""Generate fictional sample PDFs into samples/. Run once after cloning.

    docker compose run --rm ingest python scripts/make_samples.py

Core-font (Helvetica) output is latin-1, which covers German umlauts. The Euro
sign is not in latin-1, so amounts use "EUR".
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

DOCS: dict[str, list[str]] = {
    "sample_invoice.pdf": [
        "ACME Supplies Ltd.",
        "123 Market Street, London EC1A 1BB",
        "",
        "INVOICE",
        "",
        "Invoice Number: INV-2026-0042",
        "Date: 2026-05-28",
        "Bill To: Globex Corporation",
        "",
        "Consulting services      900.00",
        "Travel expenses          119.00",
        "",
        "Subtotal: 1019.00",
        "VAT (20%): 203.80",
        "Total: 1222.80 EUR",
    ],
    "sample_invoice_de.pdf": [
        "Mueller Buerobedarf GmbH",
        "Hauptstrasse 5, 10115 Berlin",
        "",
        "RECHNUNG",
        "",
        "Rechnungsnummer: RE-2026-0815",
        "Datum: 2026-05-30",
        "Kunde: Schmidt Handels AG",
        "",
        "Buerostuehle (3 Stueck)   447.00",
        "Schreibtisch              289.00",
        "",
        "Zwischensumme: 736.00",
        "MwSt (19%): 139.84",
        "Gesamtbetrag: 875.84 EUR",
    ],
    "sample_contract.pdf": [
        "SERVICE AGREEMENT",
        "",
        "This agreement is entered into between:",
        "Party A: Initech LLC",
        "Party B: Globex Corporation",
        "",
        "Effective Date: 2026-06-11",
        "Term: 12 months, auto-renewing",
        "",
        "1. Scope of services ...",
        "2. Fees and payment ...",
        "3. Termination ...",
    ],
    "sample_receipt.pdf": [
        "Cafe Central",
        "Marktplatz 2, 10178 Berlin",
        "",
        "QUITTUNG / RECEIPT",
        "Datum: 2026-05-29  14:32",
        "",
        "Cappuccino       3.80",
        "Croissant        2.40",
        "",
        "Summe: 6.20 EUR",
        "Zahlart: Karte",
    ],
    "sample_letter.pdf": [
        "Globex Corporation",
        "42 Industrial Way, Springfield",
        "",
        "2026-05-25",
        "",
        "Dear Mr. Smith,",
        "",
        "Thank you for your inquiry regarding our services.",
        "We are pleased to confirm the meeting on June 11th.",
        "",
        "Kind regards,",
        "Jane Doe",
        "Account Manager",
    ],
}


def _write(name: str, lines: list[str]) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 8, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(SAMPLES / name))
    print(f"wrote {name}")


def main() -> None:
    SAMPLES.mkdir(exist_ok=True)
    for name, lines in DOCS.items():
        _write(name, lines)


if __name__ == "__main__":
    main()
