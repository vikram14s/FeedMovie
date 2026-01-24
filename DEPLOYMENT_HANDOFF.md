# FeedMovie Deployment Handoff

**Date**: 2026-01-24
**Goal**: Connect Vercel frontend to Railway backend

---

## Current State

- [x] Railway backend is **deployed and online**
- [x] MCP servers installed: Vercel, Railway
- [ ] Connect Vercel for frontend

---

## TODO: Connect Vercel Frontend

### 1. Use Vercel MCP Server
Authenticate and connect to Vercel via the MCP server.

### 2. Create Vercel Project
- Import from GitHub: `vikram14s/FeedMovie`
- Branch: `main`
- Framework: Vite
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

### 3. Set Environment Variable
```
VITE_API_URL=<Railway backend URL>/api
```
Example: `https://feedmovie-production.up.railway.app/api`

### 4. Deploy
- Deploy the frontend to Vercel
- Get the Vercel URL

### 5. Test
- [ ] Visit Vercel URL
- [ ] Confirm it connects to Railway backend
- [ ] Test login/register
- [ ] Test recommendations

---

## Context for New Terminal

**Project location**: `/Users/adi/Documents/FeedMovie`

**Architecture**:
- **Backend (Railway)**: Python/Flask API - ALREADY DEPLOYED
- **Frontend (Vercel)**: React/Vite at `frontend/`

**MCP servers available**:
- `vercel` - Vercel deployment (HTTP transport at https://mcp.vercel.com)
- `Railway` - Railway deployment (npx @railway/mcp-server)

**GitHub**: https://github.com/vikram14s/FeedMovie (main branch)

**Frontend build**:
- Directory: `frontend/`
- Build: `npm run build`
- Output: `frontend/dist/`

---

## Notes

The frontend uses `VITE_API_URL` environment variable to know where the backend is. If not set, it defaults to `/api` (same origin). For Vercel + Railway split, it needs the full Railway URL.
