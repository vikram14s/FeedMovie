"""
Main recommendation orchestrator.

Combines:
- 80% AI Ensemble (Claude + ChatGPT + Gemini)
- 20% Collaborative Filtering (SVD)

Aggregates results by consensus and weighted scores.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from database import (get_all_ratings, add_recommendation, clear_recommendations,
                      get_watched_movie_ids, get_top_recommendations,
                      create_generation_job, update_generation_job, get_generation_job)
from ai_ensemble import get_all_ai_recommendations
from cf_engine import generate_cf_recommendations
from tmdb_client import search_movie

# Progress stages with their percentage weights
PROGRESS_STAGES = {
    'starting': 0,
    'loading_ratings': 5,
    'ai_recommendations': 10,      # AI calls start (10-60%)
    'cf_recommendations': 60,      # CF starts
    'aggregating': 70,
    'enriching_tmdb': 75,          # TMDB enrichment (75-90%)
    'genre_diversity': 90,
    'saving': 95,
    'completed': 100
}


def aggregate_recommendations(
    ai_results: Dict[str, List[Dict[str, Any]]],
    cf_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Aggregate recommendations from all sources with weighted scoring.

    Weights (with all 3 AI models):
    - Claude: 27% (80% / 3)
    - ChatGPT: 27% (80% / 3)
    - Gemini: 26% (80% / 3)
    - CF: 20%

    Weights (with only Claude + Gemini):
    - Claude: 40% (80% / 2)
    - Gemini: 40% (80% / 2)
    - CF: 20%

    Bonus: +10% per additional source that suggests same movie (consensus)
    """
    print("\n🎯 Aggregating recommendations...")

    # Normalize movie titles for matching
    def normalize_title(title: str) -> str:
        return title.lower().strip().replace(':', '').replace('-', '')

    # Group recommendations by movie
    movie_scores = defaultdict(lambda: {
        'title': None,
        'year': None,
        'score': 0.0,
        'sources': [],
        'reasons': [],
        'tmdb_id': None,
        'streaming': None
    })

    # Determine AI model weights based on which models are active
    active_ai_models = [k for k, v in ai_results.items() if v]
    num_ai_models = len(active_ai_models)

    if num_ai_models == 0:
        ai_weight_per_model = 0.0
    else:
        ai_weight_per_model = 0.80 / num_ai_models  # 80% split among active models

    weights = {model: ai_weight_per_model for model in active_ai_models}

    print(f"   AI model weights: {num_ai_models} active models × {ai_weight_per_model:.2f} = 0.80 total")
    print(f"   Active models: {', '.join(active_ai_models)}")

    for source, recs in ai_results.items():
        weight = weights.get(source, 0.0)
        for rec in recs:
            title = rec.get('title', '')
            year = rec.get('year')
            key = (normalize_title(title), year)

            movie_scores[key]['title'] = title
            movie_scores[key]['year'] = year
            movie_scores[key]['score'] += weight
            # Only add source if not already present
            if source not in movie_scores[key]['sources']:
                movie_scores[key]['sources'].append(source)
            # Only add reasoning if not empty and not already added
            reasoning = rec.get('reasoning', '')
            if reasoning and reasoning not in movie_scores[key]['reasons']:
                movie_scores[key]['reasons'].append(reasoning)
            if 'streaming' in rec:
                movie_scores[key]['streaming'] = rec.get('streaming')

    # Process CF recommendations
    for rec in cf_results:
        title = rec.get('title', '')
        year = rec.get('year')
        key = (normalize_title(title), year)

        movie_scores[key]['title'] = title
        movie_scores[key]['year'] = year
        movie_scores[key]['score'] += 0.20  # 20% weight
        # Only add CF source if not already present
        if 'cf' not in movie_scores[key]['sources']:
            movie_scores[key]['sources'].append('cf')
        # Only add reasoning if not empty and not already added
        reasoning = rec.get('reasoning', '')
        if reasoning and reasoning not in movie_scores[key]['reasons']:
            movie_scores[key]['reasons'].append(reasoning)
        movie_scores[key]['tmdb_id'] = rec.get('tmdb_id')

    # Apply consensus bonus
    for key, data in movie_scores.items():
        num_sources = len(data['sources'])
        if num_sources > 1:
            consensus_bonus = (num_sources - 1) * 0.1
            data['score'] += consensus_bonus
            print(f"   +{consensus_bonus:.1f} consensus bonus for {data['title']} (from {num_sources} sources)")

    # Sort by score
    ranked = sorted(movie_scores.values(), key=lambda x: x['score'], reverse=True)

    print(f"\n✅ Aggregated {len(ranked)} unique movies")
    if ranked:
        print(f"   Top recommendation: {ranked[0]['title']} ({ranked[0]['year']}) - Score: {ranked[0]['score']:.2f}")
        print(f"   Sources: {', '.join(ranked[0]['sources'])}")

    return ranked


def enrich_with_tmdb(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich recommendations with TMDB data (metadata + streaming).
    """
    print("\n🎬 Enriching recommendations with TMDB data...")

    enriched = []
    for rec in recommendations:
        title = rec['title']
        year = rec['year']

        # If we have TMDB ID (from CF), fetch details directly
        if rec.get('tmdb_id'):
            print(f"   Fetching details: {title} ({year})...")
            from tmdb_client import get_movie_details
            movie_data = get_movie_details(rec['tmdb_id'])
            rec['poster_path'] = movie_data['poster_path']
            rec['genres'] = movie_data['genres']
            rec['overview'] = movie_data['overview']
            rec['streaming_providers'] = movie_data['streaming_providers']
            rec['imdb_id'] = movie_data.get('imdb_id')
            rec['tmdb_rating'] = movie_data.get('tmdb_rating')
            rec['imdb_rating'] = movie_data.get('imdb_rating')
            rec['rt_rating'] = movie_data.get('rt_rating')
            enriched.append(rec)
            print(f"      ✓ Enriched from TMDB")
        else:
            # Search TMDB by title/year
            print(f"   Searching: {title} ({year})...")
            movie_data = search_movie(title, year)
            if movie_data:
                rec['tmdb_id'] = movie_data['tmdb_id']
                rec['poster_path'] = movie_data['poster_path']
                rec['genres'] = movie_data['genres']
                rec['overview'] = movie_data['overview']
                rec['streaming_providers'] = movie_data['streaming_providers']
                rec['imdb_id'] = movie_data.get('imdb_id')
                rec['tmdb_rating'] = movie_data.get('tmdb_rating')
                rec['imdb_rating'] = movie_data.get('imdb_rating')
                rec['rt_rating'] = movie_data.get('rt_rating')
                enriched.append(rec)
                print(f"      ✓ Found on TMDB")
            else:
                print(f"      ⚠️  Not found on TMDB, skipping")

    print(f"\n✅ Enriched {len(enriched)} movies with TMDB data")
    return enriched


def ensure_genre_diversity(enriched: List[Dict[str, Any]], ratings: List[Dict[str, Any]], min_per_genre: int = 5) -> List[Dict[str, Any]]:
    """
    Ensure at least min_per_genre movies for each major genre.
    Generates additional recommendations for under-represented genres.
    """
    from collections import defaultdict

    print(f"\n🎨 Ensuring genre diversity (min {min_per_genre} per genre)...")

    # Major genres to ensure
    target_genres = ['Action', 'Comedy', 'Drama', 'Science Fiction', 'Horror', 'Romance']

    # Count current genre distribution
    genre_counts = defaultdict(list)
    for movie in enriched:
        for genre in movie.get('genres', []):
            genre_counts[genre].append(movie)

    # Show current distribution
    print("\n📊 Current genre distribution:")
    for genre in target_genres:
        count = len(genre_counts[genre])
        status = "✓" if count >= min_per_genre else "⚠️"
        print(f"   {status} {genre}: {count} movies")

    # Identify under-represented genres
    under_represented = []
    for genre in target_genres:
        current_count = len(genre_counts[genre])
        if current_count < min_per_genre:
            needed = min_per_genre - current_count
            under_represented.append((genre, needed))
            print(f"   → Need {needed} more {genre} movies")

    if not under_represented:
        print("✅ All genres have sufficient coverage!")
        return enriched

    # Generate additional recommendations for under-represented genres
    print(f"\n🔄 Generating additional recommendations for {len(under_represented)} genres...")

    from ai_ensemble import get_claude_recommendations
    existing_titles = {movie['title'].lower() for movie in enriched}

    for genre, needed in under_represented:
        print(f"\n   Generating {needed} {genre} recommendations...")

        # Create genre-specific prompt
        genre_prompt_additions = {
            'Action': 'Focus on action-packed thrillers, heists, and intense sequences.',
            'Comedy': 'Focus on witty comedies, dark humor, and feel-good films.',
            'Science Fiction': 'Focus on sci-fi, cyberpunk, space exploration, and futuristic themes.',
            'Horror': 'Focus on psychological horror, thrillers, and suspenseful films.',
            'Romance': 'Focus on romantic dramas, love stories, and relationship-focused films.',
            'Drama': 'Focus on character-driven dramas and emotional stories.'
        }

        # Get genre-specific recommendations from Claude
        try:
            import anthropic
            import json
            import os

            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            top_movies = [r['title'] for r in sorted(ratings, key=lambda x: x['rating'], reverse=True)[:10]]

            prompt = f"""Based on my movie taste (top favorites: {', '.join(top_movies)}), recommend exactly {needed + 5} {genre} movies I haven't seen.

{genre_prompt_additions.get(genre, '')}

Requirements:
- ALL movies must be primarily {genre} genre
- Match my taste profile from favorites
- Include mix of recent and classic films

Format as JSON array:
[
  {{"title": "Movie Title", "year": 2023, "reasoning": "Brief reason..."}}
]

Return only the JSON array."""

            # Use Haiku for genre-fill (faster and cheaper than Opus)
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                genre_recs = json.loads(content[start:end])

                # Enrich and add non-duplicate movies
                added = 0
                for rec in genre_recs:
                    if added >= needed:
                        break

                    title = rec.get('title', '')
                    if title.lower() in existing_titles:
                        continue

                    # Search TMDB
                    from tmdb_client import search_movie
                    movie_data = search_movie(title, rec.get('year'))

                    if movie_data and genre in movie_data.get('genres', []):
                        # Add to enriched list
                        movie_data['score'] = 0.5  # Lower score for genre-fill movies
                        movie_data['sources'] = ['claude-genre-fill']
                        movie_data['reasons'] = [rec.get('reasoning', '')]
                        enriched.append(movie_data)
                        existing_titles.add(title.lower())
                        added += 1
                        print(f"      ✓ Added: {title}")

                print(f"   ✅ Added {added} {genre} movies")

        except Exception as e:
            print(f"   ❌ Error generating {genre} recommendations: {e}")

    # Show final distribution
    genre_counts = defaultdict(int)
    for movie in enriched:
        for genre in movie.get('genres', []):
            genre_counts[genre] += 1

    print(f"\n📊 Final genre distribution:")
    for genre in target_genres:
        count = genre_counts[genre]
        status = "✓" if count >= min_per_genre else "⚠️"
        print(f"   {status} {genre}: {count} movies")

    return enriched


def generate_and_save_recommendations(count: int = 15, user_id: int = None, job_id: int = None):
    """
    Main entry point: Generate recommendations from all sources and save to database.

    Args:
        count: Number of recommendations to generate
        user_id: User ID to generate recommendations for (None for legacy single-user mode)
        job_id: Optional job ID for progress tracking
    """
    def update_progress(stage: str, progress: int = None):
        """Update job progress if job_id provided."""
        if job_id:
            prog = progress if progress is not None else PROGRESS_STAGES.get(stage, 0)
            update_generation_job(job_id, stage=stage, progress=prog)
            print(f"   [Progress: {prog}%] {stage}")

    print("\n" + "=" * 60)
    print("🎬 FEEDMOVIE RECOMMENDATION ENGINE")
    print("=" * 60)
    if user_id:
        print(f"   Generating for user_id: {user_id}")

    update_progress('starting')

    update_progress('loading_ratings')

    # Load user ratings
    ratings = get_all_ratings(user_id=user_id)
    if not ratings:
        print("\n❌ No ratings found in database!")
        print("   Please run: python backend/letterboxd_import.py <csv_file>")
        if job_id:
            update_generation_job(job_id, status='failed', error_message='No ratings found')
        return

    print(f"\n📊 Loaded {len(ratings)} ratings from Letterboxd")
    print(f"   Average rating: {sum(r['rating'] for r in ratings) / len(ratings):.1f}★")

    update_progress('ai_recommendations')

    # Get AI recommendations (80% weight)
    # Each model generates 20 recommendations for diversity
    ai_results = get_all_ai_recommendations(ratings, count_per_model=20)

    update_progress('cf_recommendations')

    # Get CF recommendations (20% weight)
    cf_results = generate_cf_recommendations(count=15)

    update_progress('aggregating')

    # Aggregate all recommendations
    aggregated = aggregate_recommendations(ai_results, cf_results)

    update_progress('enriching_tmdb')

    # Enrich with TMDB data
    enriched = enrich_with_tmdb(aggregated[:count])

    update_progress('genre_diversity')

    # Ensure genre diversity: at least 5 movies per major genre
    enriched = ensure_genre_diversity(enriched, ratings, min_per_genre=5)

    update_progress('saving')

    # Ensure minimum total recommendations (25)
    MIN_TOTAL = 25
    if len(enriched) < MIN_TOTAL:
        print(f"\n⚠️  Only {len(enriched)} recommendations, need at least {MIN_TOTAL}")
        print("   Fetching more from AI to meet minimum...")
        # Get more from aggregated list if available
        additional_needed = MIN_TOTAL - len(enriched)
        existing_tmdb_ids = {m.get('tmdb_id') for m in enriched if m.get('tmdb_id')}

        for rec in aggregated[count:count + additional_needed * 2]:
            if len(enriched) >= MIN_TOTAL:
                break
            title = rec['title']
            year = rec.get('year')
            movie_data = search_movie(title, year)
            if movie_data and movie_data['tmdb_id'] not in existing_tmdb_ids:
                movie_data['score'] = rec['score']
                movie_data['sources'] = rec.get('sources', [])
                movie_data['reasons'] = rec.get('reasons', [])
                enriched.append(movie_data)
                existing_tmdb_ids.add(movie_data['tmdb_id'])
                print(f"   ✓ Added: {title}")

    print(f"\n✅ Final count: {len(enriched)} recommendations (min {MIN_TOTAL} required)")

    # Clear old recommendations for this user
    clear_recommendations(user_id=user_id)

    # Save to database
    print(f"\n💾 Saving {len(enriched)} recommendations to database...")
    watched_ids = set(get_watched_movie_ids(user_id=user_id))

    # Separate unwatched and already-watched movies
    unwatched = []
    already_watched = []

    for rec in enriched:
        if rec.get('tmdb_id') in watched_ids:
            already_watched.append(rec)
        else:
            unwatched.append(rec)

    # Calculate how many watched movies to include (max 40% of total)
    max_watched_count = int(count * 0.4)
    watched_to_include = already_watched[:max_watched_count]

    print(f"   Found {len(unwatched)} unwatched + {len(already_watched)} already-watched movies")
    print(f"   Including {len(watched_to_include)} already-watched movies (≤40% of total)")

    # Save unwatched movies first
    saved_count = 0
    from database import add_movie, add_recommendation

    for rec in unwatched:
        # Determine primary source for database
        sources = rec.get('sources', [])
        primary_source = sources[0] if sources else 'unknown'

        # Use only the first reasoning (from primary source) to avoid redundancy
        all_reasons = rec.get('reasons', [])
        reasoning = all_reasons[0] if all_reasons else ''

        # Add to database
        movie_id = add_movie(
            tmdb_id=rec['tmdb_id'],
            title=rec['title'],
            year=rec.get('year'),
            genres=rec.get('genres', []),
            poster_path=rec.get('poster_path'),
            streaming_providers=rec.get('streaming_providers', {}),
            overview=rec.get('overview', ''),
            imdb_id=rec.get('imdb_id'),
            tmdb_rating=rec.get('tmdb_rating'),
            imdb_rating=rec.get('imdb_rating'),
            rt_rating=rec.get('rt_rating')
        )

        add_recommendation(
            movie_id=movie_id,
            source=primary_source,
            score=rec['score'],
            reasoning=reasoning,
            user_id=user_id
        )
        saved_count += 1

    # Then add already-watched movies toward the end
    for rec in watched_to_include:
        sources = rec.get('sources', [])
        primary_source = sources[0] if sources else 'unknown'
        all_reasons = rec.get('reasons', [])
        reasoning = all_reasons[0] if all_reasons else ''

        movie_id = add_movie(
            tmdb_id=rec['tmdb_id'],
            title=rec['title'],
            year=rec.get('year'),
            genres=rec.get('genres', []),
            poster_path=rec.get('poster_path'),
            streaming_providers=rec.get('streaming_providers', {}),
            overview=rec.get('overview', ''),
            imdb_id=rec.get('imdb_id'),
            tmdb_rating=rec.get('tmdb_rating'),
            imdb_rating=rec.get('imdb_rating'),
            rt_rating=rec.get('rt_rating')
        )

        add_recommendation(
            movie_id=movie_id,
            source=primary_source,
            score=rec['score'] * 0.5,  # Lower score so they appear later
            reasoning=reasoning,
            user_id=user_id
        )
        saved_count += 1
        print(f"   Added already-watched: {rec['title']}")

    print(f"   ✅ Saved {saved_count} recommendations ({len(unwatched)} new + {len(watched_to_include)} watched)")

    # Show summary
    print("\n" + "=" * 60)
    print("✅ RECOMMENDATION GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\nGenerated {saved_count} recommendations")
    print(f"Next step: python backend/app.py to start the web server")
    print(f"Or query database: sqlite3 data/feedmovie.db")

    # Mark job as completed
    if job_id:
        update_generation_job(job_id, status='completed', progress=100)
        print(f"   [Progress: 100%] completed")


if __name__ == '__main__':
    generate_and_save_recommendations(count=50)  # Increased to ensure min 25 after genre diversity
