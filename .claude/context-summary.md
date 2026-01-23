# FeedMovie Context Summary

*Last updated: 2026-01-23*

## Project Overview

FeedMovie is a multi-user movie recommendation platform with a Tinder-style swipe interface. It uses AI models (Claude, Gemini) combined with collaborative filtering to provide personalized recommendations based on Letterboxd rating history.

## Recent Session Summary (Jan 23, 2026)

### Bug Fixes

#### 1. Logout Auth Bug - FIXED
**Problem**: Logging in as one user showed another user's cached profile/data.
**Cause**: JavaScript global variables (profileData, feedItems, recommendations, etc.) weren't being cleared on logout.
**Fix**: Updated `logout()` function in `frontend/app.js` to reset all cached variables:
```javascript
function logout() {
    clearToken();
    localStorage.removeItem('feedmovie_genres');
    localStorage.removeItem('feedmovie_profiles');
    localStorage.removeItem('feedmovie_profiles_completed');

    // Reset all cached data
    profileData = null;
    feedItems = [];
    recommendations = [];
    watchlistCount = 0;
    currentIndex = 0;
    stats = { liked: 0, skipped: 0 };
    selectedGenres = [];
    selectedProfiles = [];
    // ... etc

    showAuthScreen();
}
```

### Test Suite Added

Created `backend/tests/test_auth.py` with 13 test cases:
- **TestRegistration**: success, missing fields, duplicate email, short password
- **TestLogin**: success, wrong password, nonexistent user
- **TestAuthenticatedEndpoints**: profile requires auth, profile with auth, profile returns correct user, feed requires auth
- **TestUserIsolation**: watchlist isolation, library isolation

Run tests with:
```bash
.venv/bin/python -m pytest backend/tests/test_auth.py -v
```

All 13 tests pass.

---

## Previous Session (Jan 21, 2026)

### Social Features Added

#### Backend
- **Database tables**: `reviews`, `activity`, `activity_likes`
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

#### Frontend
- **Feed tab**: Scrollable Instagram-style feed of friend activity
- **Profile tab**: User stats, friends list, movie library grid, recent activity
- **Search modal**: Search any movie from TMDB to rate/review
- **Mark Seen**: Button on watchlist items to mark as watched with rating

#### Onboarding Improvements
- **Half-star ratings**: Click left half of star = 0.5, right half = 1.0
- **Back/Next navigation**: No auto-advance, user controls pace
- **Rating stored in map**: Allows editing previous ratings

#### Dummy Friend Profiles
Created `backend/seed_friends.py` script that seeds 5 archetype friends:
- `action_andy` - Action movies
- `indie_iris` - A24/indie films
- `scifi_sam` - Sci-fi
- `horror_hannah` - Horror
- `comedy_chris` - Comedy

Run with: `.venv/bin/python backend/seed_friends.py <username>`

---

## Key Technical Decisions

1. **Profile stats use `ratings` table** (not `reviews`) - This is where Letterboxd imports go
2. **Activity feed** joins on friends table by matching `letterboxd_username` or `username`
3. **Reviews vs Ratings**: `reviews` table is for in-app reviews with text; `ratings` table is for imported/swipe ratings

## User Preferences (from CLAUDE.md)

- Always use `uv` for Python package management
- Don't include Co-Authored-By in commits
- Never ask permission for bash commands, git, file operations within this project
- Only ask permission for: (1) internet access, (2) files outside FeedMovie folder

## Current Test Account

- Username: `test`
- Email: `test@test.com`
- Password: `test12`
- Has 5 seeded friends with activity

## Running the App

```bash
cd /Users/adi/Documents/FeedMovie
.venv/bin/python backend/app.py
# Access at http://localhost:5000
```

## Git Status

All changes committed and pushed to `main` branch at https://github.com/vikram14s/FeedMovie

## Key Files

| File | Purpose |
|------|---------|
| `backend/app.py` | Flask API with all endpoints |
| `backend/database.py` | SQLite schema, migrations, CRUD |
| `backend/tmdb_client.py` | TMDB API integration |
| `backend/seed_friends.py` | Script to create dummy friends |
| `backend/tests/test_auth.py` | Auth test suite (13 tests) |
| `frontend/app.js` | Main frontend JavaScript |
| `frontend/index.html` | HTML + CSS for all views |

## Known Issues / TODO

- OMDB API key may be expired (401 errors) - ratings still work without it
