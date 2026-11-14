import io
import os
import docx
import pymupdf
import pytest

from app.parsers.chunker import chunk_text
from app.parsers.csv_parser import parse_approved_facts_csv
from app.parsers.docx_parser import parse_docx
from app.parsers.pdf_parser import parse_pdf


def test_chunk_text():
    sample_text = (
        "BrandSentinel is an enterprise governance platform. It checks content before publication. "
        "Our core principle is AI suggests, humans decide. Every finding must have a source citation.\n\n"
        "This is paragraph two. It contains additional brand requirements and guidelines for marketers."
    )
    chunks = chunk_text(sample_text, chunk_size=120, overlap=30, page_number=1)
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert "BrandSentinel" in chunks[0].content


def test_parse_approved_facts_csv():
    csv_data = """category,claim_pattern,approved_truth,mandatory_caveat,source_citation
Performance,Cost savings,Average infrastructure cost reduction is up to 30%,Measured over 6 months,Q4 Benchmarks p. 12
Pricing,Enterprise tier,Enterprise plans start at $1200/mo,Billed annually,Pricing Guide 2026
"""
    facts = parse_approved_facts_csv(csv_data)
    assert len(facts) == 2
    assert facts[0]["category"] == "Performance"
    assert facts[0]["approved_truth"] == "Average infrastructure cost reduction is up to 30%"
    assert facts[0]["source_citation"] == "Q4 Benchmarks p. 12"
    assert facts[1]["category"] == "Pricing"


def test_pdf_parsing(tmp_path):
    # Generate a real PDF with PyMuPDF
    pdf_path = str(tmp_path / "test_guidelines.pdf")
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "Acme Brand Guidelines\nSection 1: Voice and Tone.")
    page1.insert_text((50, 120), "Never use hyperbolic promises such as '50% cheaper overnight'.")
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf(pdf_path, extract_images=False)
    assert parsed.page_count == 1
    assert "Acme Brand Guidelines" in parsed.full_text
    assert "50% cheaper overnight" in parsed.full_text
    assert len(parsed.chunks) >= 1


def test_docx_parsing(tmp_path):
    # Generate a real DOCX with python-docx
    docx_path = str(tmp_path / "test_policy.docx")
    doc = docx.Document()
    doc.add_heading("Social Media Guidelines", level=1)
    doc.add_paragraph("All public posts must declare their language and provide descriptive alt text.")
    doc.save(docx_path)

    parsed = parse_docx(docx_path, extract_images=False)
    assert "Social Media Guidelines" in parsed.full_text
    assert "descriptive alt text" in parsed.full_text
    assert len(parsed.chunks) >= 1
