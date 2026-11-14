# API Specification — BrandSentinel

Base URL: `/api/v1`

## 1. Authentication & Identity (`/auth`)
- `POST /auth/register` — Create organization & admin user.
- `POST /auth/login` — Authenticate and receive JWT access token.
- `GET /auth/me` — Retrieve active user profile, organization info, and role permissions.

## 2. Brand Knowledge Management (`/knowledge`)
- `POST /knowledge/guidelines/upload` — Ingest PDF/DOCX guidelines, generate chunks & embeddings.
- `GET /knowledge/guidelines` — List uploaded guidelines.
- `POST /knowledge/facts` — Create an approved factual statement.
- `POST /knowledge/facts/import-csv` — Bulk upload approved facts from CSV.
- `GET /knowledge/facts` — List approved facts.
- `POST /knowledge/glossary` — Add glossary term or banned word.
- `GET /knowledge/glossary` — List glossary terms.
- `POST /knowledge/assets` — Upload brand asset (logo or hex palette).
- `GET /knowledge/assets` — List brand assets.

## 3. Auditing & Findings (`/audit`)
- `POST /audit/run` — Run Tri-Engine audit on raw text or uploaded document.
- `GET /audit/submissions` — List user/organization submissions.
- `GET /audit/submissions/{id}` — Fetch submission detail, versions, and findings.

## 4. Governance & Decisions (`/governance`)
- `POST /governance/findings/{id}/decide` — Record Creator action (`ACCEPTED`, `EDITED`, `REJECTED`).
- `POST /governance/submissions/{id}/comments` — Add reviewer comment.
- `POST /governance/submissions/{id}/sign-off` — Reviewer/Manager approval or rejection.
- `GET /governance/submissions/{id}/export` — Export approved version with governance certificate.

## 5. Analytics (`/analytics`)
- `GET /analytics/dashboard` — Aggregated compliance scores, top violations, and guideline gaps.
