# Database Schema — BrandSentinel

The persistence tier is built with SQLAlchemy 2.0 (async). It supports PostgreSQL (with pgvector) in production and seamless local SQLite/PostgreSQL development.

## 1. Entity Relationships

- **Organizations (Tenants)**: Isolates all enterprise data.
- **Users**: Bound to an organization with RBAC (`CREATOR`, `REVIEWER`, `BRAND_MANAGER`, `ADMIN`).
- **Guidelines**: Uploaded PDF/DOCX policy documents.
- **Document Chunks**: Decomposed semantic text chunks with vector embeddings.
- **Approved Facts**: Structured factual statements with citations.
- **Glossary Terms**: Permitted and banned terminology.
- **Brand Assets**: Approved logos and official color hex palettes.
- **Submissions**: Content drafts queued for review.
- **Content Versions**: Immutable revisions of submitted content with image metadata.
- **Findings**: Issues detected across all 3 engines with source citations and fixes.
- **Finding Decisions**: Human decisions (`ACCEPTED`, `EDITED`, `REJECTED`) with reasons.
- **Review Comments**: Reviewer annotations and escalations.
- **Audit Logs**: Tamper-evident activity logs.

## 2. Multi-Tenancy Design
Every query filters on `organization_id`. The FastAPI dependency `get_current_active_user` injects the authenticated organization context into repository queries, preventing cross-tenant data leaks.
