# FeedMovie Deployment Handoff

**Date**: 2026-01-24
**Status**: COMPLETE

---

## Deployed URLs

- **Frontend (Vercel)**: https://feed-movie.vercel.app/
- **Backend (Railway)**: https://feedmovie-production.up.railway.app/api

---

## Architecture

```
[Vercel - Frontend]          [Railway - Backend]
React/Vite app        --->   Python/Flask API
feed-movie.vercel.app        feedmovie-production.up.railway.app
```

## Environment Variables

**Vercel (frontend)**:
- `VITE_API_URL` = `https://feedmovie-production.up.railway.app/api`

**Railway (backend)**:
- `TMDB_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `JWT_SECRET`

---

## Testing Checklist

- [x] Backend health check: `/api/health` returns `{"status":"ok"}`
- [ ] Visit https://feed-movie.vercel.app/
- [ ] Test login/register
- [ ] Test recommendations

---

## GitHub

- Repo: https://github.com/vikram14s/FeedMovie
- Branch: `main`

## Files Added

- `frontend/vercel.json` - Vercel build config
- `railway.toml` - Railway build config
