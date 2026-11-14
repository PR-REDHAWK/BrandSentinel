# System Architecture — BrandSentinel

## 1. High-Level Architecture

BrandSentinel operates as a multi-tenant enterprise system sitting between content creation and publication.

```
+-------------------------------------------------------------------------------+
|                            NEXT.JS 15 FRONTEND                                |
|  - Creator Studio (Diffs, Suggestions)       - Review Queue (Severity Ranked) |
|  - Brand Knowledge Hub (Guidelines, Assets)  - Governance Insights Dashboard  |
+-------------------------------------------------------------------------------+
                                      |  (REST API / JWT Auth)
                                      v
+-------------------------------------------------------------------------------+
|                             FASTAPI BACKEND                                   |
|  - JWT Authentication & RBAC                 - Document Ingestion Pipeline    |
|  - Organization Data Isolation               - Audit Orchestrator             |
+-------------------------------------------------------------------------------+
         |                                    |                        |
         v                                    v                        v
+------------------+                +------------------+     +------------------+
| DETERMINISTIC    |                |    RAG + LLM     |     |   VISION + OCR   |
| ENGINE           |                |      ENGINE      |     |      ENGINE      |
| - Banned Words   |                | - Vector Retr.   |     | - OCR text       |
| - Glossary Terms |                | - Fact Verify    |     | - Color Palette  |
| - WCAG 2.2 Math  |                | - Tone & Voice   |     | - Logo Check     |
+------------------+                +------------------+     +------------------+
         |                                    |                        |
         +------------------+                 |                        |
                            v                 v                        v
                    +-----------------------------------------------------------+
                    |             UNIFIED FINDING AGGREGATOR                    |
                    | Normalizes schemas, computes brand score, enforces checks |
                    +-----------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                          PERSISTENT STORAGE TIER                              |
|  PostgreSQL 18 + Vector Store (Embeddings, Guidelines, Submissions, Logs)    |
+-------------------------------------------------------------------------------+
```

## 2. Core Architectural Principles
1. **No Finding Without Evidence:** Every factual finding MUST be anchored to an uploaded guideline chunk or approved fact row.
2. **AI Suggests, Humans Decide:** The platform never modifies or publishes content automatically.
3. **Deterministic First:** Exact rules (banned phrases, WCAG ratios) execute deterministically without LLM inference latency or nondeterminism.
4. **Tenant Isolation:** Every table carries `organization_id` enforced at the query level.
