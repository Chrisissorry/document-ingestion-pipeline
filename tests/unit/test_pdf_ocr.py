from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

import ingest.tools.pdf as pdf

SAMPLES = Path(__file__).resolve().parent.parent.parent / "samples"
TEXT_PDF = str(SAMPLES / "sample_invoice.pdf")
SCAN_PDF = str(SAMPLES / "sample_invoice_scan.pdf")


# --- render_page_image ----------------------------------------------------


def test_render_page_image_returns_a_pil_image() -> None:
    img = pdf.render_page_image(SCAN_PDF)
    assert isinstance(img, Image.Image)
    assert img.width > 0 and img.height > 0


# --- ocr_available: the env flag gate -------------------------------------


def test_ocr_unavailable_when_flag_unset(monkeypatch) -> None:
    monkeypatch.delenv(pdf.OCR_ENV_FLAG, raising=False)
    assert pdf.ocr_available() is False


@pytest.mark.parametrize("falsey", ["", "0", "false", "no", "off", "anything-else"])
def test_ocr_unavailable_for_falsey_flag_values(monkeypatch, falsey) -> None:
    monkeypatch.setenv(pdf.OCR_ENV_FLAG, falsey)
    assert pdf.ocr_available() is False


@pytest.mark.parametrize("truthy", ["1", "true", "TRUE", "yes", "on", " on "])
def test_ocr_available_when_flag_on_and_binary_present(monkeypatch, truthy) -> None:
    monkeypatch.setenv(pdf.OCR_ENV_FLAG, truthy)
    # Stand in for the optional pytesseract package; get_tesseract_version() not raising
    # is what "binary present" looks like.
    fake = SimpleNamespace(get_tesseract_version=lambda: "5.3.0")
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    assert pdf.ocr_available() is True


def test_ocr_unavailable_when_package_missing(monkeypatch) -> None:
    monkeypatch.setenv(pdf.OCR_ENV_FLAG, "1")
    # Simulate the extra not being installed: importing pytesseract raises.
    monkeypatch.setitem(sys.modules, "pytesseract", None)
    assert pdf.ocr_available() is False


def test_ocr_unavailable_when_binary_missing(monkeypatch) -> None:
    monkeypatch.setenv(pdf.OCR_ENV_FLAG, "1")

    # Package imports, but the Tesseract binary is absent / broken.
    def _boom() -> str:
        raise OSError("tesseract is not installed or it's not in your PATH")

    fake = SimpleNamespace(get_tesseract_version=_boom)
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    assert pdf.ocr_available() is False


# --- ocr_first_page -------------------------------------------------------


def test_ocr_first_page_returns_stripped_text(monkeypatch) -> None:
    fake = MagicMock()
    fake.image_to_string.return_value = "  INVOICE\nTotal: 100 EUR  \n"
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    out = pdf.ocr_first_page(SCAN_PDF)
    assert out == "INVOICE\nTotal: 100 EUR"
    # It must OCR a rendered page image, not raw bytes.
    (image_arg,), _ = fake.image_to_string.call_args
    assert isinstance(image_arg, Image.Image)
