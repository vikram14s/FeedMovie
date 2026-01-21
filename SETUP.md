# FeedMovie Setup Guide

Complete guide to get FeedMovie running this weekend.

## Prerequisites

- Python 3.10+ with uv installed
- Your Letterboxd data exported
- 4 API keys (see below)

## Step 1: Get API Keys (30 minutes)

### 1.1 TMDB API Key (Free)
1. Go to https://www.themoviedb.org/
2. Create account
3. Go to Settings → API → Request API Key
4. Choose "Developer"
5. Fill out form (can use personal project info)
6. Copy your API Key (v3 auth)

### 1.2 Anthropic API Key (Claude)
1. Go to https://console.anthropic.com/
2. Sign up (new accounts get $5 credit)
3. Go to API Keys
4. Create new key
5. Copy the key

### 1.3 OpenAI API Key (ChatGPT)
1. Go to https://platform.openai.com/
2. Sign up
3. Add payment method (pay-as-you-go, ~$0.05 per session)
4. Go to API Keys
5. Create new secret key
6. Copy the key

### 1.4 Google AI API Key (Gemini)
1. Go to https://ai.google.dev/
2. Sign in with Google account
3. Click "Get API key"
4. Create new API key
5. Copy the key

**Cost estimate:** ~$1-2 for testing with 50 recommendations

## Step 2: Export Letterboxd Data (5 minutes)

1. Log in to Letterboxd
2. Go to Settings → Import & Export
3. Click "Export Your Data"
4. Wait for email with download link
5. Download the ZIP file
6. Extract `ratings.csv` to `data/letterboxd/ratings.csv`

## Step 3: Configure Environment (2 minutes)

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
TMDB_API_KEY=your_actual_tmdb_key_here
ANTHROPIC_API_KEY=your_actual_anthropic_key_here
OPENAI_API_KEY=your_actual_openai_key_here
GOOGLE_API_KEY=your_actual_google_key_here
```

## Step 4: Install Dependencies (5 minutes)

```bash
# uv will automatically create venv and install dependencies
uv pip install -r requirements.txt
```

## Step 5: Initialize Database (1 minute)

```bash
uv run backend/database.py
```

Expected output:
```
Database initialized at data/feedmovie.db
Database setup complete!
```

## Step 6: Import Your Letterboxd Data (5-10 minutes)

```bash
uv run backend/letterboxd_import.py data/letterboxd/ratings.csv
```

This will:
- Parse your ratings CSV
- Search TMDB for each movie
- Fetch metadata + streaming availability
- Save to database

Expected output:
```
Importing Letterboxd data from data/letterboxd/ratings.csv...
  [1/96] Searching for 'Blade Runner 2049' (2017)...
    ✓ Added to DB (ID: 1)
  ...
✅ Import complete!
   Total rows: 96
   Imported: 86
   Skipped: 10
   Success rate: 89.6%
```

**Note:** ~90% match rate is normal. Some obscure titles won't be found in TMDB.

## Step 7: Generate Recommendations (5-10 minutes)

**This is the most important step!**

```bash
uv run backend/recommender.py
```

This will:
1. Load your ratings from database
2. Call Claude, ChatGPT, and Gemini for AI recommendations
3. Train simple CF model and generate CF recommendations
4. Aggregate all results with weighted scoring
5. Enrich with TMDB data (streaming availability)
6. Save top 50 to database

Expected output:
```
=========================================================
🎬 FEEDMOVIE RECOMMENDATION ENGINE
=========================================================

📊 Loaded 86 ratings from Letterboxd
   Average rating: 4.2★

🤖 Getting recommendations from Claude (with web search)...
   ✓ Got 15 recommendations from Claude
🤖 Getting recommendations from ChatGPT...
   ✓ Got 15 recommendations from ChatGPT
🤖 Getting recommendations from Gemini...
   ✓ Got 15 recommendations from Gemini

📊 Training CF model on 86 ratings...
   ✓ CF model trained successfully
📊 Generating 15 CF recommendations...
   ✓ Generated 15 CF recommendations

🎯 Aggregating recommendations...
   +0.2 consensus bonus for Dune: Part Two (from 3 sources)
   ...

✅ Aggregated 45 unique movies
   Top recommendation: Dune: Part Two (2024) - Score: 0.87
   Sources: claude, chatgpt, gemini

🎬 Enriching recommendations with TMDB data...
   Searching: Dune: Part Two (2024)...
      ✓ Found on TMDB
   ...

💾 Saving 45 recommendations to database...
   ✅ Saved 45 recommendations

=========================================================
✅ RECOMMENDATION GENERATION COMPLETE!
=========================================================

Generated 45 recommendations
Next step: python backend/app.py to start the web server
```

**Troubleshooting:**
- If API errors: Check your .env keys are correct
- If TMDB rate limit: Wait 10 seconds and retry
- If < 10 ratings: CF won't work well, but AI models will still work

## Step 8: Start the Web Server

```bash
uv run backend/app.py
```

Expected output:
```
🎬 Starting FeedMovie API server...
🌐 Frontend: http://localhost:5000
📡 API: http://localhost:5000/api/recommendations

✨ Happy movie hunting!

 * Running on http://0.0.0.0:5000
```

## Step 9: Open in Browser

Open http://localhost:5000

You should see:
- Your first recommendation as a card
- Movie poster, title, year, genres
- Streaming availability badges (Netflix, Prime, etc.)
- AI reasoning for why you'd like it
- Swipe buttons (❌ left to skip, ✅ right to like)

**Controls:**
- Click ❌ or press ← or X to skip
- Click ✅ or press → or V to like
- Swipe through all 50 recommendations!

## Verification Checklist

### Backend ✓
- [ ] Database created at `data/feedmovie.db`
- [ ] Letterboxd ratings imported (check with: `sqlite3 data/feedmovie.db "SELECT COUNT(*) FROM ratings;"`)
- [ ] Recommendations generated (check with: `sqlite3 data/feedmovie.db "SELECT COUNT(*) FROM recommendations;"`)
- [ ] Flask server running on port 5000

### Frontend ✓
- [ ] Can access http://localhost:5000
- [ ] See movie card with poster
- [ ] See streaming availability badges
- [ ] Can swipe left/right
- [ ] Stats update (Remaining, Liked, Skipped)

### End-to-End ✓
- [ ] Swipe through 10 movies
- [ ] Check swipes recorded: `sqlite3 data/feedmovie.db "SELECT COUNT(*) FROM recommendations WHERE swipe_action IS NOT NULL;"`
- [ ] Should show 10

## Common Issues

### "TMDB_API_KEY not set"
- Make sure `.env` file exists in project root
- Check API key is correct (no extra spaces/quotes)

### "No ratings found in database"
- Run `letterboxd_import.py` first
- Check CSV file is at correct path

### "No CF recommendations"
- Need at least 5 ratings for CF to work
- AI recommendations will still work

### "API rate limit"
- TMDB: Wait 10 seconds, has 0.25s delay between requests
- AI APIs: Shouldn't hit limits for MVP usage

### Frontend shows "Failed to connect"
- Make sure Flask server is running
- Check port 5000 isn't blocked
- Try http://localhost:5000 instead of 127.0.0.1

## Next Steps

Once everything works:

1. **Swipe through your recommendations**
   - Rate which ones you like
   - Feedback is recorded for future improvements

2. **Generate more recommendations**
   - Re-run `backend/recommender.py` anytime
   - Can increase count: edit `recommender.py` line with `count=50` to `count=100`

3. **Add friends' data**
   - Ask friends to export their Letterboxd CSVs
   - Run importer with `--user friend_name` flag (to be implemented)
   - Will improve CF recommendations

4. **Deploy to cloud**
   - Use Vercel/Railway for free hosting
   - Make accessible anywhere
   - Add authentication for multi-user

5. **Improve swipe feedback loop**
   - Currently just records swipes
   - Future: automatically retrain models based on swipes
   - Personalize even further

## Need Help?

Check logs:
```bash
# Backend logs (Flask)
uv run backend/app.py

# Database inspection
sqlite3 data/feedmovie.db
sqlite> .tables
sqlite> SELECT * FROM recommendations LIMIT 5;

# Test TMDB connection
uv run backend/tmdb_client.py

# Test AI ensemble
uv run backend/ai_ensemble.py
```

Happy movie hunting! 🎬
