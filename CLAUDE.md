# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FeedMovie is an AI-powered movie recommendation system with a Tinder-like swipe interface. It combines multiple AI models (Claude Opus 4.5, Gemini 3 Pro, optionally ChatGPT) with collaborative filtering (SVD) to provide personalized recommendations based on Letterboxd rating history.

## Common Commands

```bash
# Install dependencies (prefer uv)
uv pip install -r requirements.txt

# Initialize database (first time only)
uv run backend/database.py

# Import Letterboxd ratings
uv run backend/letterboxd_import.py data/letterboxd/ratings.csv

# Import a friend's ratings
uv run backend/friends_import.py "Friend Name" data/letterboxd/friend_ratings.csv

# Generate recommendations (calls AI APIs, takes a few minutes)
uv run backend/recommender.py

# Start the Flask server (serves both API and frontend)
uv run backend/app.py
# Access at http://localhost:5000

# Database inspection
sqlite3 data/feedmovie.db ".tables"
sqlite3 data/feedmovie.db "SELECT COUNT(*) FROM ratings;"
sqlite3 data/feedmovie.db "SELECT COUNT(*) FROM recommendations;"
```

## Architecture

**Backend (Python 3.9+ / Flask)**
- `backend/app.py` - Flask API server, serves frontend static files
- `backend/recommender.py` - Main orchestrator, combines AI + CF results
- `backend/ai_ensemble.py` - Claude, ChatGPT, Gemini API integrations
- `backend/cf_engine.py` - Collaborative filtering using scikit-surprise SVD
- `backend/tmdb_client.py` - TMDB API client with diskcache caching
- `backend/database.py` - SQLite setup and queries
- `backend/letterboxd_import.py` - CSV importer for Letterboxd exports

**Frontend (Vanilla JS)**
- `frontend/index.html` - Single-page app with embedded CSS
- `frontend/app.js` - Swipe logic, API calls, state management
- `frontend/logos/` - Local streaming service brand assets

**Data**
- `data/feedmovie.db` - SQLite database
- `data/cache/` - TMDB API response cache
- `data/letterboxd/` - User CSV exports

## Recommendation Algorithm

Weights:
- AI Ensemble: 80% total (split evenly among active models)
- Collaborative Filtering: 20%

Consensus bonus: +10% per additional source suggesting the same movie.

Already-watched movies can be included (max 40% of total, scored at 0.5x to appear later).

## Database Schema

- `movies` - TMDB data, streaming_providers (JSON), genres (JSON)
- `ratings` - User/friend ratings (0.5-5.0 scale)
- `recommendations` - AI/CF results with source, score, reasoning, swipe_action
- `friends` - Friend names with compatibility scores
- `settings` - Key-value store for preferences

## API Endpoints

- `GET /api/recommendations` - Fetch recommendations (params: limit, genres)
- `POST /api/swipe` - Record swipe action (body: tmdb_id, action)
- `POST /api/add-rating` - Add rating for watched movie
- `GET /api/watchlist` - Get liked movies
- `DELETE /api/watchlist/{tmdb_id}` - Remove from watchlist
- `POST /api/generate-more` - Trigger background recommendation generation

## Environment Variables (.env)

```
TMDB_API_KEY=      # Required - themoviedb.org
ANTHROPIC_API_KEY= # Required for Claude
GOOGLE_API_KEY=    # Required for Gemini
OPENAI_API_KEY=    # Optional for ChatGPT
OMDB_API_KEY=      # Optional for IMDb/RT ratings
```

## Key Implementation Details

- Frontend uses local logos from `frontend/logos/` (not TMDB URLs)
- Streaming services are deduplicated; rental-only shows "$" badge
- Genre filtering is strict (no fallback to all movies)
- Background recommendation generation runs in separate thread
- TMDB responses cached in `data/cache/` to avoid rate limits
- Keyboard shortcuts: ← skip, → like, S for "already seen" modal

## Allowed Commands

These bash commands are pre-approved for Claude Code in this project:

```
uv run backend/app.py
uv run backend/recommender.py
uv run backend/database.py
uv run backend/letterboxd_import.py
uv run backend/friends_import.py
uv pip install -r requirements.txt
sqlite3 data/feedmovie.db
kill (for stopping server processes)
lsof -i :5000 (for checking port usage)
```
