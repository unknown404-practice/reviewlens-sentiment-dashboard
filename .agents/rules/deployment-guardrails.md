---
description: Guardrails for full-stack cloud deployment, Python container dependencies, Vercel monorepo roots, and CORS origin hygiene.
globs: ["requirements.txt", "backend/**", "frontend-next/**", ".github/**"]
---

# Full-Stack Deployment Guardrails

## 1. Python Cloud Dependency Verification
- Before deploying or packaging Python microservices for cloud container platforms (Render, Railway, Fly.io, Heroku):
  - Audit all imports across the codebase (`import <pkg>`, `from <pkg> import ...`).
  - Verify that every third-party import is explicitly specified in `requirements.txt` (especially split packages such as `pydantic-settings` alongside `pydantic`, and `beautifulsoup4` for `bs4`).
  - Never assume local environment installations are automatically reflected in `requirements.txt`.

## 2. Vercel Subdirectory & Monorepo Deployments
- When deploying a Next.js frontend situated in a subfolder (e.g., `frontend-next/`):
  - Always verify and explicitly set **Root Directory** = `frontend-next` during project configuration.
  - Ensure `NEXT_PUBLIC_*` environment variables pointing to backend APIs omit trailing slashes (`/`).

## 3. CORS Cross-Service Handshake
- When connecting Vercel frontends to Render/FastAPI backends:
  - Configure `ALLOWED_ORIGINS` on the backend without trailing slashes.
  - When `allow_credentials=False`, recommend `*` or exact comma-separated origins to permit preview deployments and custom domains seamlessly.
