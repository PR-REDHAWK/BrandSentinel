# BrandSentinel

**Intelligent Brand-Governance Platform**
*AI suggests. Humans decide. No finding without a cited source. No automatic publishing.*

BrandSentinel is an enterprise-grade brand governance platform that reviews content before publication across four pillars:
1. **Factual Accuracy & Claim Verification:** Grounded against approved fact sheets and benchmarks using RAG with hard source citations.
2. **Brand Guidelines & Tone:** Evaluated for voice, banned terms, and glossary conformity.
3. **Accessibility Compliance:** WCAG 2.2 Level AA contrast (4.5:1 text, 3:1 graphical elements), alt-text presence, and language declarations.
4. **Visual & Brand Asset Consistency:** Color palette tolerances, logo compliance, and banner text OCR.

---

## Architecture Overview

BrandSentinel employs a **Tri-Engine Auditing Pipeline**:
- **Deterministic Rule Engine:** High-speed regex term boundary scanners, WCAG 2.2 color contrast formulas, and accessibility tags.
- **RAG + LLM Grounding Engine:** Google Gemini integrated with strict citation boundaries and structured Pydantic schemas. Unreferenced claims are rejected.
- **Vision + OCR Engine:** Pillow, Tesseract OCR / Multimodal Vision fallback, and CIELAB color-distance matching.

---

## Quickstart

### Backend Setup (FastAPI + Python 3.12)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup (Next.js 15 + Tailwind CSS)
```bash
cd frontend
npm install
npm run dev
```

---

## Documentation
- [System Architecture](ARCHITECTURE.md)
- [Database Schema & ER Diagrams](DATABASE.md)
- [API Contract Specification](API.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Architectural Decisions](DECISIONS.md)
