# FeedMovie

AI-powered movie recommendation system with Tinder-like swipe interface. Solves the streaming service limitation problem by recommending movies across ALL platforms with availability info.

## Features

- 🤖 AI Ensemble: Claude Opus 4.5 + Gemini 3 Pro (with Google Search grounding)
- 📊 Collaborative Filtering: 20% weight using your Letterboxd data
- 📺 Streaming Availability: Shows Netflix, Prime, HBO Max, etc.
- 👆 Swipe Interface: Tinder-like UI for easy decision making
- 🎯 Personalized: Based on your Letterboxd rating history
- 🔍 Web-Enhanced: Gemini 3 Pro uses Google Search to find current streaming info and recent films

## Quick Start

### 1. Get API Keys

You'll need these API keys:

- **TMDB**: https://themoviedb.org (free) - Required
- **Anthropic**: https://console.anthropic.com ($5 credit for new accounts) - Required for Claude Opus 4.5
- **Google AI**: https://ai.google.dev (free tier) - Required for Gemini 3 Pro
- **OpenAI**: https://platform.openai.com (pay as you go) - Optional, add ChatGPT later if desired

### 2. Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Import Your Letterboxd Data

1. Export your Letterboxd data: Settings → Import & Export → Export Your Data
2. Save the ratings.csv file to `data/letterboxd/ratings.csv`
3. Run the importer:

```bash
python backend/letterboxd_import.py data/letterboxd/ratings.csv
```

### 4. Generate Recommendations

```bash
# Generate recommendations (takes a few minutes)
python backend/recommender.py

# Start the web server
python backend/app.py

# Open http://localhost:5000 in your browser
```

## Project Structure

```
feedmovie/
├── data/
│   ├── letterboxd/      # Your CSV exports
│   ├── feedmovie.db     # SQLite database
│   └── cache/           # TMDB cache
├── backend/
│   ├── database.py
│   ├── letterboxd_import.py
│   ├── tmdb_client.py
│   ├── ai_ensemble.py
│   ├── cf_engine.py
│   ├── recommender.py
│   └── app.py
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## How It Works

1. **Import**: Loads your Letterboxd ratings into SQLite
2. **AI Ensemble**: Claude, ChatGPT, and Gemini each analyze your taste and recommend movies
3. **Collaborative Filtering**: Simple SVD model finds patterns in your ratings
4. **Aggregation**: Combines all recommendations, scores by consensus
5. **Streaming Data**: TMDB provides availability across all major platforms
6. **Swipe UI**: Interactive interface to rate recommendations

## Cost

- TMDB: Free
- Gemini 3 Pro: Free tier available
- Claude Opus 4.5: ~$0.50 per recommendation session (15 movies)
- Total for MVP testing: ~$2-3 (covered by Anthropic's $5 new account credit)

## Future Enhancements

- Add friends' Letterboxd data for better CF
- Swipe feedback loop to improve recommendations
- Deploy to cloud (Vercel/Railway)
- Multi-user support with authentication
- Mobile app

## License

MIT
