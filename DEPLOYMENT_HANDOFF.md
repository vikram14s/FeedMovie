# FeedMovie Deployment Handoff

**Date**: 2026-01-24
**Goal**: Deploy FeedMovie for 5-6 beta testers

---

## Prerequisites Done

- [x] Railway config merged (`railway.toml`, `.env.example`)
- [x] Frontend builds to `frontend/dist/`
- [x] Backend serves from dist with SPA routing
- [x] MCP servers installed: Vercel, Railway

---

## TODO: Deploy to Railway

### 1. Authenticate with Railway MCP
```
Use the Railway MCP server to authenticate and connect to Railway
```

### 2. Create New Project
- Create a new Railway project called "feedmovie"
- Connect to GitHub repo: `vikram14s/FeedMovie`
- Branch: `main`

### 3. Set Environment Variables
Add these in Railway dashboard or via MCP:
```
ANTHROPIC_API_KEY=<from local .env>
GOOGLE_API_KEY=<from local .env>
TMDB_API_KEY=<from local .env>
JWT_SECRET=<generate with: openssl rand -hex 32>
```

Optional:
```
OPENAI_API_KEY=<if available>
```

### 4. Add Persistent Volume
- Mount path: `/app/data`
- This persists the SQLite database between deploys

### 5. Deploy & Get URL
- Trigger deploy from main branch
- Get the public URL (e.g., `feedmovie-production.up.railway.app`)

### 6. Test the Deployment
- [ ] Visit the URL, see login screen
- [ ] Register a new account
- [ ] Complete onboarding (Letterboxd or swipe)
- [ ] Get recommendations
- [ ] Test social features (search users, view profiles)

---

## Context for New Terminal

**Project location**: `/Users/adi/Documents/FeedMovie`

**Tech stack**:
- Backend: Python/Flask (`backend/app.py`)
- Frontend: React/Vite (`frontend/`) - builds to `frontend/dist/`
- Database: SQLite at `data/feedmovie.db`

**Key files**:
- `railway.toml` - Railway build config
- `.env.example` - Required environment variables
- `backend/app.py` - Uses PORT env var, serves frontend

**MCP servers available**:
- `vercel` - Vercel deployment (HTTP transport)
- `Railway` - Railway deployment (npx @railway/mcp-server)

**GitHub**: https://github.com/vikram14s/FeedMovie (main branch)

---

## After Deployment

Share with testers:
1. The Railway URL
2. Instructions to register an account
3. Optional: Their Letterboxd username for import

---

## Rollback

If something goes wrong:
```bash
# Railway dashboard: Deployments > select previous > Redeploy
# Or via CLI/MCP: rollback to previous deployment
```
