"""
Taste Analyzer - Extract rich context from user's Letterboxd data.

Analyzes ratings to build a comprehensive taste profile for better AI prompts.
"""

import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from database import get_connection


def analyze_rating_distribution(ratings: List[Dict]) -> Dict[str, Any]:
    """
    Analyze user's rating behavior.

    Returns:
        {
            "avg_rating": 3.8,
            "std_dev": 0.9,
            "total_count": 90,
            "rating_style": "selective",  # generous, balanced, selective, harsh
            "distribution": {5.0: 12, 4.5: 18, 4.0: 25, ...},
            "percentiles": {"loved": 4.5, "liked": 4.0, "meh": 3.0}
        }
    """
    if not ratings:
        return {"total_count": 0, "rating_style": "unknown"}

    scores = [r['rating'] for r in ratings]
    avg = sum(scores) / len(scores)

    # Calculate standard deviation
    variance = sum((x - avg) ** 2 for x in scores) / len(scores)
    std_dev = variance ** 0.5

    # Determine rating style
    if avg >= 4.2:
        style = "generous"
    elif avg >= 3.8:
        style = "balanced"
    elif avg >= 3.4:
        style = "selective"
    else:
        style = "harsh"

    # Build distribution
    distribution = defaultdict(int)
    for score in scores:
        distribution[score] += 1

    # Calculate percentiles for what counts as "loved", "liked", etc.
    sorted_scores = sorted(scores, reverse=True)
    percentile_90 = sorted_scores[int(len(sorted_scores) * 0.1)] if len(sorted_scores) > 10 else 5.0
    percentile_70 = sorted_scores[int(len(sorted_scores) * 0.3)] if len(sorted_scores) > 3 else 4.0
    percentile_30 = sorted_scores[int(len(sorted_scores) * 0.7)] if len(sorted_scores) > 3 else 3.0

    return {
        "avg_rating": round(avg, 2),
        "std_dev": round(std_dev, 2),
        "total_count": len(ratings),
        "rating_style": style,
        "distribution": dict(sorted(distribution.items(), reverse=True)),
        "percentiles": {
            "loved": percentile_90,
            "liked": percentile_70,
            "meh": percentile_30
        }
    }


def extract_anti_preferences(ratings: List[Dict], threshold: float = 2.5) -> Dict[str, Any]:
    """
    Extract patterns from low-rated movies to identify what to AVOID.

    Returns:
        {
            "disliked_genres": ["Romance", "Musical"],
            "avoided_themes": ["predictable plot", "slow pacing"],
            "low_rated_examples": ["Movie1 (2.0)", "Movie2 (1.5)"]
        }
    """
    low_rated = [r for r in ratings if r['rating'] <= threshold]

    if not low_rated:
        return {"disliked_genres": [], "avoided_themes": [], "low_rated_examples": []}

    # Count genres in low-rated movies
    genre_counts = defaultdict(int)
    for r in low_rated:
        genres = r.get('genres', [])
        if isinstance(genres, str):
            try:
                genres = json.loads(genres)
            except:
                genres = []
        for genre in genres:
            genre_counts[genre] += 1

    # Get genres that appear frequently in low-rated movies
    total_low = len(low_rated)
    disliked_genres = [
        genre for genre, count in genre_counts.items()
        if count >= 2 and count / total_low >= 0.3  # At least 30% of low-rated
    ]

    # Example movies
    low_rated_examples = [
        f"{r['title']} ({r['rating']}★)"
        for r in sorted(low_rated, key=lambda x: x['rating'])[:5]
    ]

    return {
        "disliked_genres": disliked_genres,
        "avoided_themes": [],  # Will be populated when we have TMDB keywords
        "low_rated_examples": low_rated_examples
    }


def extract_director_actor_patterns(ratings: List[Dict]) -> Dict[str, List[str]]:
    """
    Find favorite directors and actors from highly-rated movies.

    Requires TMDB credits data. For now, returns empty if not available.
    This will be enhanced when we add credits fetching.

    Returns:
        {
            "favorite_directors": ["Christopher Nolan", "Denis Villeneuve"],
            "favorite_actors": ["Ryan Gosling", "Margot Robbie"]
        }
    """
    # This requires TMDB credits API - will be populated in later phase
    # For now, return empty to not break the flow
    return {
        "favorite_directors": [],
        "favorite_actors": []
    }


def extract_genre_preferences(ratings: List[Dict]) -> Dict[str, float]:
    """
    Calculate genre preference scores based on ratings.

    Returns dict of genre -> average rating for that genre.
    """
    genre_ratings = defaultdict(list)

    for r in ratings:
        genres = r.get('genres', [])
        if isinstance(genres, str):
            try:
                genres = json.loads(genres)
            except:
                genres = []
        for genre in genres:
            genre_ratings[genre].append(r['rating'])

    # Calculate average rating per genre
    genre_scores = {}
    for genre, scores in genre_ratings.items():
        if len(scores) >= 3:  # Need minimum sample size
            genre_scores[genre] = round(sum(scores) / len(scores), 2)

    # Sort by score descending
    return dict(sorted(genre_scores.items(), key=lambda x: x[1], reverse=True))


def calculate_decade_preferences(ratings: List[Dict]) -> Dict[str, float]:
    """
    Analyze preference by decade.

    Returns dict of decade -> average rating.
    """
    decade_ratings = defaultdict(list)

    for r in ratings:
        year = r.get('year')
        if year:
            decade = f"{(year // 10) * 10}s"
            decade_ratings[decade].append(r['rating'])

    # Calculate average rating per decade
    decade_scores = {}
    for decade, scores in decade_ratings.items():
        if len(scores) >= 3:  # Need minimum sample size
            decade_scores[decade] = round(sum(scores) / len(scores), 2)

    return dict(sorted(decade_scores.items(), key=lambda x: x[0], reverse=True))


def get_recent_watches(ratings: List[Dict], days: int = 30) -> List[Dict]:
    """
    Get movies watched in the last N days.
    """
    cutoff = datetime.now() - timedelta(days=days)

    recent = []
    for r in ratings:
        watched_date = r.get('watched_date')
        if watched_date:
            try:
                if isinstance(watched_date, str):
                    watch_dt = datetime.strptime(watched_date, '%Y-%m-%d')
                else:
                    watch_dt = watched_date
                if watch_dt >= cutoff:
                    recent.append(r)
            except:
                pass

    return sorted(recent, key=lambda x: x.get('watched_date', ''), reverse=True)


def get_top_rated_movies(ratings: List[Dict], min_rating: float = 4.5, limit: int = 15) -> List[Dict]:
    """
    Get user's top-rated movies.
    """
    top = [r for r in ratings if r['rating'] >= min_rating]
    return sorted(top, key=lambda x: x['rating'], reverse=True)[:limit]


def build_taste_profile(ratings: List[Dict]) -> Dict[str, Any]:
    """
    Build comprehensive taste profile from all ratings.

    This is the main function that combines all analysis.
    """
    if not ratings:
        return {"error": "No ratings available"}

    # Get top movies for favorites analysis
    top_movies = get_top_rated_movies(ratings, min_rating=4.0, limit=15)

    profile = {
        "rating_behavior": analyze_rating_distribution(ratings),
        "genre_preferences": extract_genre_preferences(ratings),
        "decade_preferences": calculate_decade_preferences(ratings),
        "anti_preferences": extract_anti_preferences(ratings),
        "director_actor_patterns": extract_director_actor_patterns(ratings),
        "recent_watches": get_recent_watches(ratings, days=60),
        "top_movies": [
            {
                "title": r['title'],
                "year": r.get('year'),
                "rating": r['rating'],
                "genres": r.get('genres', [])
            }
            for r in top_movies
        ]
    }

    return profile


def format_taste_profile_for_prompt(profile: Dict[str, Any]) -> str:
    """
    Format taste profile as text for AI prompt.
    """
    lines = []

    # Rating behavior
    rb = profile.get('rating_behavior', {})
    if rb.get('total_count', 0) > 0:
        lines.append(f"### Rating Behavior")
        lines.append(f"- Average rating: {rb.get('avg_rating', 'N/A')}/5 (you are a {rb.get('rating_style', 'balanced')} rater)")
        lines.append(f"- Total movies rated: {rb.get('total_count', 0)}")
        lines.append(f"- Your 'loved it' threshold: {rb.get('percentiles', {}).get('loved', 4.5)}+ stars")
        lines.append("")

    # Top movies
    top = profile.get('top_movies', [])
    if top:
        lines.append("### Top Favorites")
        for m in top[:10]:
            genres_str = ', '.join(m.get('genres', [])[:3]) if isinstance(m.get('genres'), list) else ''
            lines.append(f"- {m['title']} ({m.get('year', 'N/A')}) - {m['rating']}★ [{genres_str}]")
        lines.append("")

    # Genre preferences
    gp = profile.get('genre_preferences', {})
    if gp:
        top_genres = list(gp.items())[:5]
        lines.append("### Favorite Genres (by avg rating)")
        for genre, score in top_genres:
            lines.append(f"- {genre}: {score}★ avg")
        lines.append("")

    # Decade preferences
    dp = profile.get('decade_preferences', {})
    if dp:
        lines.append("### Decade Preferences")
        for decade, score in list(dp.items())[:4]:
            lines.append(f"- {decade}: {score}★ avg")
        lines.append("")

    # Anti-preferences
    anti = profile.get('anti_preferences', {})
    disliked = anti.get('disliked_genres', [])
    examples = anti.get('low_rated_examples', [])
    if disliked or examples:
        lines.append("### ANTI-PREFERENCES (Things to AVOID)")
        if disliked:
            lines.append(f"- Genres you often rate low: {', '.join(disliked)}")
        if examples:
            lines.append(f"- Low-rated examples: {', '.join(examples[:3])}")
        lines.append("")

    # Recent watches
    recent = profile.get('recent_watches', [])
    if recent:
        lines.append("### Recent Watches (Last 60 Days)")
        for m in recent[:5]:
            lines.append(f"- {m['title']} ({m['rating']}★)")
        lines.append("")

    return '\n'.join(lines)


if __name__ == '__main__':
    # Test with real data
    from database import get_all_ratings

    ratings = get_all_ratings()
    print(f"Analyzing {len(ratings)} ratings...\n")

    profile = build_taste_profile(ratings)

    print("=" * 60)
    print("TASTE PROFILE")
    print("=" * 60)
    print(format_taste_profile_for_prompt(profile))
