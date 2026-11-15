# BrandSentinel — Production Deployment Guide

This guide provides step-by-step instructions for deploying BrandSentinel live to production.

---

## Architecture Overview

BrandSentinel consists of three coordinated production components:
1. **Frontend (Next.js 15, React 19, Tailwind CSS)**: User dashboard, tri-engine interactive audit workbench, governance workflows.
2. **Backend (FastAPI, Python 3.12, PyMuPDF, python-docx, Tesseract OCR, Pillow)**: Tri-engine auditing orchestrator, JWT auth, RBAC, Gemini RAG integration.
3. **Database (PostgreSQL 16 + pgvector or SQLite fallback)**: Multi-tenant schemas, embeddings, version-locked audit trail.

---

## Option 1: 1-Click Cloud Deployment via Render Blueprint (Recommended)

Render can automatically provision the PostgreSQL database, the Dockerized FastAPI backend (with Tesseract OCR pre-installed), and the Next.js frontend using the included `render.yaml` blueprint.

### Steps:
1. Push your latest code to GitHub:
   ```bash
   git add .
   git commit -m "Configure production deployment"
   git push origin main
   ```
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** in the top right, then select **Blueprint**.
4. Connect your GitHub repository: `PR-REDHAWK/BrandSentinel`.
5. Render will detect `render.yaml` and display the 3 services:
   - `brandsentinel-db` (PostgreSQL)
   - `brandsentinel-api` (FastAPI Docker web service)
   - `brandsentinel-frontend` (Next.js Docker web service)
6. Under `brandsentinel-api`, input your secret environment variable:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
7. Click **Apply**.
8. Render will build and deploy all services. Once finished, you will receive two public HTTPS URLs:
   - Frontend: `https://brandsentinel-frontend.onrender.com`
   - Backend API Docs: `https://brandsentinel-api.onrender.com/docs`
9. Because `AUTO_SEED=true` is pre-configured, the demo organization (`Acme Corporation`) and accounts (`admin@acme.com`, `reviewer@acme.com`, `creator@acme.com` / `Password123!`) will be ready immediately.

---

## Option 2: Hybrid Deployment (Vercel Frontend + Render Backend)

This is the fastest combination for high-speed edge loading.

### Step 1: Deploy Backend on Render or Railway
1. In Render, select **New + > Web Service**.
2. Connect your repo and choose **Docker** runtime (using `backend/Dockerfile`, Root Directory: `backend`).
3. Set Environment Variables:
   - `GEMINI_API_KEY`: `<your_gemini_api_key>`
   - `ENVIRONMENT`: `production`
   - `AUTO_SEED`: `true`
   - `CORS_ORIGINS`: `*`
   - `DATABASE_URL`: Your PostgreSQL connection string (or use default persistent volume SQLite).
4. Note your live backend URL (e.g. `https://brandsentinel-api.onrender.com`).

### Step 2: Deploy Frontend on Vercel
1. Log in to [Vercel](https://vercel.com) and click **Add New Project**.
2. Import `PR-REDHAWK/BrandSentinel`.
3. In Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
4. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://brandsentinel-api.onrender.com/api/v1`
5. Click **Deploy**.
6. Within 60 seconds, your site is live with a global custom URL (e.g. `https://brandsentinel.vercel.app`).

---

## Option 3: Single VPS / Cloud Server with Docker Compose

Deploy on any Linux server (AWS EC2, DigitalOcean Droplet, GCP Compute Engine, Hetzner, etc.):

1. SSH into your server:
   ```bash
   ssh user@your-server-ip
   ```
2. Clone repository:
   ```bash
   git clone https://github.com/PR-REDHAWK/BrandSentinel.git
   cd BrandSentinel
   ```
3. Create environment file `backend/.env`:
   ```bash
   cat << 'EOF' > backend/.env
   ENVIRONMENT=production
   DEBUG=false
   GEMINI_API_KEY=your_gemini_api_key_here
   AUTO_SEED=true
   CORS_ORIGINS=*
   EOF
   ```
4. Start all services with Docker Compose:
   ```bash
   docker compose up -d --build
   ```
5. Verify services are healthy:
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```
6. (Optional) Point your domain name with Nginx or Caddy for automatic Let's Encrypt SSL:
   ```caddy
   brandsentinel.yourdomain.com {
       reverse_proxy localhost:3000
   }
   api.brandsentinel.yourdomain.com {
       reverse_proxy localhost:8000
   }
   ```

---

## Option 4: Instant Public Live Tunnel (Cloudflare Tunnel / ngrok)

If you need a public URL immediately for live hackathon judges without provisioning cloud infrastructure:

### Using Cloudflare Tunnel (Zero Sign-up, Completely Free):
1. Start your backend and frontend locally:
   - Backend: `uvicorn app.main:app --port 8000` (inside `backend`)
   - Frontend: `npm run dev` (inside `frontend`)
2. In a separate terminal, install and run Cloudflare Tunnel:
   ```bash
   # Download cloudflared or run via npx:
   npx cloudflared tunnel --url http://localhost:3000
   ```
3. Cloudflare outputs a public HTTPS link (e.g. `https://random-words.trycloudflare.com`). Anyone worldwide can access your live application.

---

## Pre-Seeded Hackathon Demo Credentials

When `AUTO_SEED=true` is enabled, the following accounts are available on first startup:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@acme.com` | `Password123!` | Full governance, user administration, tenant settings |
| **Reviewer** | `reviewer@acme.com` | `Password123!` | Review queue, findings audit, official sign-off |
| **Creator** | `creator@acme.com` | `Password123!` | Create submissions, accept/edit/reject findings |
