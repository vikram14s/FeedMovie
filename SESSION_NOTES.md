# FeedMovie Development Session Notes
*Last Updated: January 9, 2026*

## Project Overview
FeedMovie is an AI-powered movie recommendation system with a Tinder-like swipe interface. It combines multiple AI models (Claude, Gemini, ChatGPT) with collaborative filtering to provide personalized movie recommendations across all streaming platforms.

## Architecture
- **Backend**: Flask (Python 3.9)
  - AI Ensemble: 80% weight (Claude Opus 4.5 + Gemini 3 Pro + ChatGPT)
  - Collaborative Filtering: 20% weight (SVD algorithm)
  - TMDB API integration for movie metadata and streaming availability
  - SQLite database for ratings, recommendations, and user data

- **Frontend**: HTML/CSS/JS
  - Spotify-inspired dark theme
  - Swipe interface with keyboard shortcuts
  - Local streaming service logos
  - Watchlist feature

## Recent Changes (This Session)

### 1. Streaming Service Logos
- **Fixed**: Now using local logos from `frontend/logos/` instead of TMDB
- **Logos available**: Netflix, Amazon Prime, Apple TV, Hulu, YouTube, Fandango, Google Play Movies
- **Styling**: 32px height, brightness filter (1.1x), proper spacing (gap-3)
- **Deduplication**: Services only appear once even if in both subscription and rental
- **Rental indicator**: Shows green "$" badge under logo for rental-only services
- **Filtered out**: FlixFling (removed from display)

### 2. Already-Watched Movies Feature
- **Implementation**: Includes movies user has already rated in recommendations
- **Limit**: Maximum 40% of total recommendations
- **Placement**: Lower scores (0.5x multiplier) so they appear toward the end
- **Visual indicator**: "Already watched" badge on card
- **Database**: Uses `get_watched_movie_ids()` to check against ratings table

### 3. "See More" Button
- **Location**: Shows when user finishes all recommendations
- **Functionality**: Generates fresh recommendations using swipe feedback
- **API Endpoint**: `POST /api/generate-more`
- **Behavior**: Triggers `generate_and_save_recommendations()` and reloads page

### 4. Cleaned Up Reasoning Text
- **Fixed duplicate reasoning**: Changed from concatenating all AI outputs to using only primary source
- **SQL query**: Changed from `GROUP_CONCAT(r.reasoning, ' | ')` to `MAX(r.reasoning)`
- **Aggregation**: Added deduplication logic to prevent same reasoning appearing twice
- **Result**: Clean, single reasoning text per movie

### 5. Removed Emojis
- **Section headers**: "Available on:", "About:", "Why you'll love it:" (no emojis)
- **Badges**: "Already watched" (no emoji)
- **Kept emojis**: Only in source badges (🤖 claude, 💎 gemini, etc.)

### 6. Fixed Genre Filtering
- **Previous behavior**: If <5 movies matched selected genre, showed ALL movies
- **New behavior**: Shows ONLY movies matching selected genre (even if just 1-2)
- **Logic**: Removed fallback in `get_top_recommendations()` that returned all when filtered list was small

### 7. Fixed Duplicate Source Badges
- **Backend**: Added deduplication in aggregation logic (checks if source already in list)
- **SQL**: Added `DISTINCT` to `GROUP_CONCAT(DISTINCT r.source)`
- **Frontend**: Added `[...new Set(sources)]` deduplication

## Current File Structure
```
feedmovie/
├── data/
│   ├── letterboxd/ratings.csv
│   ├── feedmovie.db
│   └── cache/                    # TMDB cache
├── backend/
│   ├── database.py              # SQLite setup + queries
│   ├── letterboxd_import.py     # CSV importer
│   ├── tmdb_client.py           # TMDB API client
│   ├── ai_ensemble.py           # Claude + ChatGPT + Gemini
│   ├── cf_engine.py             # Collaborative filtering (SVD)
│   ├── recommender.py           # Main orchestrator
│   └── app.py                   # Flask API
├── frontend/
│   ├── index.html               # UI structure + CSS
│   ├── app.js                   # Swipe logic + API calls
│   └── logos/                   # Local streaming service logos
│       ├── Netflix.png
│       ├── Amazon-Prime-Video-Icon.png
│       ├── AppleTVLogo.png
│       ├── Hulu.png
│       ├── Youtube_logo.png
│       ├── Fandango.svg
│       └── google-play-movies-tv-logo.png
├── requirements.txt
├── .env                         # API keys
└── SESSION_NOTES.md            # This file
```

## Database Schema

### movies
- `id`, `tmdb_id`, `title`, `year`, `genres` (JSON)
- `poster_path`, `streaming_providers` (JSON), `overview`

### ratings
- `id`, `movie_id`, `rating` (0.5-5.0), `watched_date`, `user`

### recommendations
- `id`, `movie_id`, `source` (claude/gemini/chatgpt/cf)
- `score`, `reasoning`, `shown_to_user`, `swipe_action`

### friends
- `id`, `name`, `letterboxd_username`, `compatibility_score`

### settings
- `key`, `value` (e.g., 'friend_recommendations_enabled')

## API Endpoints

### GET /api/recommendations
- Query params: `limit` (default: 50), `genres` (comma-separated)
- Returns: List of unwatched recommendations with TMDB data

### POST /api/swipe
- Body: `{"tmdb_id": 123, "action": "left|right"}`
- Records user's swipe action

### POST /api/add-rating
- Body: `{"tmdb_id": 123, "title": "Movie", "year": 2023, "rating": 4.5}`
- Adds rating for already-seen movie from watchlist

### GET /api/watchlist
- Returns: Movies user has liked (swiped right on)

### DELETE /api/watchlist/{tmdb_id}
- Removes movie from watchlist

### POST /api/generate-more
- Generates fresh recommendations using swipe feedback
- Clears old recommendations and creates new batch

## Recommendation Algorithm

### Weights (with 2 active AI models)
- Claude: 40% (80% / 2)
- Gemini: 40% (80% / 2)
- ChatGPT: 0% (API key invalid)
- CF: 20%

### Consensus Bonus
- +10% per additional source that suggests same movie
- Example: Movie from Claude + Gemini = 0.40 + 0.40 + 0.10 = 0.90 score

### Already-Watched Movies
- Included at max 40% of total
- Score multiplied by 0.5 to appear later
- Reasoning unchanged (no prefix added)

## Key Functions

### `backend/recommender.py`
- `aggregate_recommendations()`: Combines AI + CF results with weighted scoring
- `enrich_with_tmdb()`: Adds TMDB metadata and streaming providers
- `generate_and_save_recommendations()`: Main entry point

### `backend/database.py`
- `get_top_recommendations()`: Fetches recommendations with genre filtering
- `add_movie()`: Adds movie with TMDB data (deduplicates by tmdb_id)
- `record_swipe()`: Updates recommendation with user action

### `frontend/app.js`
- `createStreamingBadges()`: Renders logos with deduplication and rental indicators
- `getLocalLogo()`: Maps service names to local logo files
- `generateMoreRecommendations()`: Calls API to generate fresh recommendations

## Environment Variables (.env)
```
TMDB_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Currently invalid
GOOGLE_API_KEY=your_key_here
```

## Current Status

### Working Features
✅ AI-powered recommendations (Claude + Gemini)
✅ Collaborative filtering
✅ Local streaming service logos with rental indicators
✅ Already-watched movie inclusion (max 40%)
✅ "See More" button for fresh recommendations
✅ Clean, non-duplicate reasoning text
✅ Genre filtering (strict - no fallback)
✅ Watchlist with swipe tracking
✅ Keyboard shortcuts (← skip, S already seen, → like)
✅ Modal for rating already-seen movies

### Known Issues
🔧 ChatGPT API key is invalid (401 error)
🔧 Python 3.9 end-of-life warnings (Google/urllib3)
🔧 LibreSSL warning (not critical)

### Pending Features/Improvements
- Friends feature (database schema ready, not implemented)
- Python version upgrade (3.9 → 3.11/3.12)
- Recommendation refinement based on swipe feedback (API exists but not utilized)

## Running the Application

### Start Flask Server
```bash
uv run backend/app.py
```
Server runs on: http://localhost:5000

### Generate Recommendations
```bash
uv run backend/recommender.py
```

### Import Letterboxd Data
```bash
uv run backend/letterboxd_import.py data/letterboxd/ratings.csv
```

## User Data
- **Total ratings**: 183 movies
- **Average rating**: 4.0★
- **Watched movies**: 93
- **Current recommendations**: ~14 movies (11 unwatched + 2-4 already-watched)

## Notes for Future Development
1. Consider implementing swipe-based learning (use yes/no data to refine future recs)
2. Add friends compatibility feature using Pearson correlation
3. Update Python to 3.11+ to remove deprecation warnings
4. Consider caching AI responses to reduce API costs
5. Add more streaming service logos as needed
6. Consider adding filters for streaming availability (e.g., "Only Netflix")

## Frontend Design Notes
- **Color scheme**: Dark theme (#121212 background, #1DB954 Spotify green accents)
- **Typography**: System fonts, clean and readable
- **Card design**: 650px height, rounded corners, shadow effects
- **Responsive**: Works on desktop (not optimized for mobile yet)
- **Animation**: Smooth swipe transitions using CSS transforms

## Recent Session Activities

### Design & Layout Improvements
1. **Wider Card Layout**: Increased container from max-w-2xl (640px) to max-w-4xl (896px)
2. **Fixed Poster Aspect Ratio**: Set poster height to 450px (proper 2:3 movie poster ratio)
3. **Card Height**: Increased from 700px to 800px for better content display
4. **TMDB Ratings**: Yellow star rating badge showing TMDB score (0-10 scale)
5. **IMDb Integration**: Clickable IMDb badge linking to movie page (opens in new tab)
6. **Database Schema**: Added columns for imdb_id, tmdb_rating, imdb_rating, rt_rating
7. Complete frontend redesign with atmospheric gradient background (blues, purples, teals)
8. New typography: DM Sans (modern geometric sans-serif)
9. Glass morphism design with frosted glass cards and backdrop blur
10. Staggered fade-in animations on page load

### Performance & UX Improvements
11. **Smart Loading System**:
   - Backend generates 30 movies, stores in database with shown_to_user flag
   - Frontend fetches only 10 movies at a time (not overwhelming)
   - Database keeps 20 in reserve for instant "See More"
   - Preemptively triggers generation when <15 unshown remain in database
   - Background generation in separate thread (non-blocking)
   - "See More" instantly loads next 10 from database (no waiting)
   - Genre preferences saved to localStorage for persistent sessions
12. **Genre Distribution**:
   - Ensures minimum 5 movies per selected genre
   - Better genre bucket distribution algorithm
   - Smarter filtering when multiple genres selected
13. **AI Model Tuning**:
   - Increased to 20 recommendations per AI model (was 10)
   - CF engine now generates 15 (was 10)
   - Better variety in final recommendations

### Previous Session
14. Fixed streaming logo duplicates (Apple TV appearing twice)
15. Added $ indicator for rental-only services
16. Removed FlixFling from display
17. Fixed duplicate reasoning/source badges
18. Removed emojis from section headers
19. Fixed genre filtering to be strict
