# FeedMovie Context Summary

*Last updated: 2026-01-21*

## Project Overview

FeedMovie is a multi-user movie recommendation platform with a Tinder-style swipe interface. It uses AI models (Claude, Gemini) combined with collaborative filtering to provide personalized recommendations based on Letterboxd rating history.

## Recent Session Summary (Jan 21, 2026)

### Features Added Today

#### 1. Social Features (Backend)
- **Database tables**: `reviews`, `activity`, `activity_likes` for social functionality
- **User profile fields**: `bio`, `profile_picture_url` added to users table
- **API endpoints**:
  - `GET /api/movies/search?q=` - Search TMDB for movies
  - `POST /api/reviews` - Create/update review with rating + text
  - `GET /api/feed` - Friends activity feed
  - `POST/DELETE /api/feed/<id>/like` - Like/unlike activity
  - `GET /api/profile` - User profile with stats
  - `GET /api/profile/library` - User's rated movies (Letterboxd imports)
  - `GET /api/profile/friends` - User's friends list
  - `POST /api/watchlist/<tmdb_id>/seen` - Mark watchlist item as watched

#### 2. Social Features (Frontend)
- **Feed tab**: Scrollable Instagram-style feed of friend activity
- **Profile tab**: User stats, friends list, movie library grid, recent activity
- **Search modal**: Search any movie from TMDB to rate/review
- **Mark Seen**: Button on watchlist items to mark as watched with rating

#### 3. Dummy Friend Profiles
Created `backend/seed_friends.py` script that seeds 5 archetype friends:
- `action_andy` - Action movies (Mad Max, John Wick, Top Gun Maverick)
- `indie_iris` - A24/indie (Everything Everywhere, Moonlight, Lady Bird)
- `scifi_sam` - Sci-fi (Dune, Arrival, Blade Runner 2049)
- `horror_hannah` - Horror (Hereditary, The Witch, Get Out)
- `comedy_chris` - Comedy (Grand Budapest Hotel, Barbie, Big Lebowski)

Run with: `.venv/bin/python backend/seed_friends.py <username>`

#### 4. UI Improvements
- Wider container (640px) so nav pills don't need horizontal scrolling
- Filters tab restored to nav bar
- Profile shows Letterboxd library grid and friends list

### Key Technical Decisions

1. **Profile stats use `ratings` table** (not `reviews`) - This is where Letterboxd imports go
2. **Activity feed** joins on friends table by matching `letterboxd_username` or `username`
3. **Reviews vs Ratings**: `reviews` table is for in-app reviews with text; `ratings` table is for imported/swipe ratings

### User Preferences (from CLAUDE.md)

- Always use `uv` for Python
- Don't include Co-Authored-By in commits
- Never ask permission for bash commands, git, file operations within this project
- Only ask permission for: (1) internet access, (2) files outside FeedMovie folder

### Current Test Account

- Username: `test`
- Email: `test@test.com`
- Password: `test12`
- Has 5 seeded friends with activity

### Parallel Work Setup

Created `/parallelize` custom command at `.claude/commands/parallelize.md` for setting up git worktrees to parallelize tasks across multiple Claude Code terminals.

### Files Modified Today

**Backend:**
- `backend/app.py` - Added social feature endpoints
- `backend/database.py` - Added tables, migrations, CRUD functions
- `backend/tmdb_client.py` - Added `search_movies()` function
- `backend/seed_friends.py` - NEW: Script to seed dummy friends

**Frontend:**
- `frontend/index.html` - Added Feed, Profile views, CSS for library/friends
- `frontend/app.js` - Added feed, profile, search, review functionality

### Running the App

```bash
cd /Users/adi/Documents/FeedMovie
.venv/bin/python backend/app.py
# Access at http://localhost:5000
```

### Git Status

All changes committed and pushed to `main` branch at https://github.com/vikram14s/FeedMovie

### Known Issues / TODO

- OMDB API key may be expired (401 errors) - ratings still work without it
- `/parallelize` command not being recognized by Claude Code - may need restart or different location
