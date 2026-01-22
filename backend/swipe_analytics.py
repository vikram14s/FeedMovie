"""
Swipe Analytics - Learn user preferences from swipe behavior.

Analyzes swipe patterns to understand:
- Which genres the user tends to like/skip
- Which AI sources have better accuracy
- Recency preferences (modern vs classic)
- Theme preferences

This data feeds back into AI prompts for better personalization.
"""

import json
from typing import Dict, List, Any, Optional
from collections import defaultdict
from database import get_connection


def get_swipe_patterns() -> Dict[str, Any]:
    """
    Analyze all swipe history to find patterns.

    Returns:
        {
            "liked_genres": {"Action": 0.8, "Sci-Fi": 0.75, ...},
            "skipped_genres": {"Romance": 0.7, "Animation": 0.65, ...},
            "liked_decades": {"2020s": 0.85, "2010s": 0.6, ...},
            "liked_sources": {"claude": 0.75, "gemini": 0.65, ...},
            "acceptance_rate": 0.35,
            "total_swipes": 150,
            "total_likes": 52,
            "total_skips": 98
        }
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get all swiped recommendations with movie data
    cursor.execute('''
        SELECT
            r.swipe_action,
            r.source,
            m.genres,
            m.year,
            m.title
        FROM recommendations r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.swipe_action IS NOT NULL
    ''')

    swipes = cursor.fetchall()
    conn.close()

    if not swipes:
        return {
            "total_swipes": 0,
            "liked_genres": {},
            "skipped_genres": {},
            "liked_decades": {},
            "liked_sources": {},
            "acceptance_rate": 0,
            "total_likes": 0,
            "total_skips": 0
        }

    # Initialize counters
    genre_likes = defaultdict(int)
    genre_skips = defaultdict(int)
    genre_total = defaultdict(int)

    source_likes = defaultdict(int)
    source_total = defaultdict(int)

    decade_likes = defaultdict(int)
    decade_total = defaultdict(int)

    total_likes = 0
    total_skips = 0

    for swipe in swipes:
        action = swipe['swipe_action']
        source = swipe['source']
        genres = json.loads(swipe['genres']) if swipe['genres'] else []
        year = swipe['year']

        liked = action == 'right'
        if liked:
            total_likes += 1
        else:
            total_skips += 1

        # Track by genre
        for genre in genres:
            genre_total[genre] += 1
            if liked:
                genre_likes[genre] += 1
            else:
                genre_skips[genre] += 1

        # Track by source
        source_total[source] += 1
        if liked:
            source_likes[source] += 1

        # Track by decade
        if year:
            decade = f"{(year // 10) * 10}s"
            decade_total[decade] += 1
            if liked:
                decade_likes[decade] += 1

    total_swipes = total_likes + total_skips

    # Calculate like ratios (for genres with enough data)
    def calc_ratio(likes_dict, total_dict, min_samples=3):
        return {
            k: round(likes_dict.get(k, 0) / total_dict[k], 2)
            for k in total_dict
            if total_dict[k] >= min_samples
        }

    # Calculate skip ratios
    def calc_skip_ratio(skips_dict, total_dict, min_samples=3):
        return {
            k: round(skips_dict.get(k, 0) / total_dict[k], 2)
            for k in total_dict
            if total_dict[k] >= min_samples and skips_dict.get(k, 0) / total_dict[k] > 0.5
        }

    liked_genres = calc_ratio(genre_likes, genre_total)
    skipped_genres = calc_skip_ratio(genre_skips, genre_total)

    return {
        "liked_genres": dict(sorted(liked_genres.items(), key=lambda x: x[1], reverse=True)),
        "skipped_genres": dict(sorted(skipped_genres.items(), key=lambda x: x[1], reverse=True)),
        "liked_decades": dict(sorted(calc_ratio(decade_likes, decade_total).items(), key=lambda x: x[1], reverse=True)),
        "liked_sources": dict(sorted(calc_ratio(source_likes, source_total).items(), key=lambda x: x[1], reverse=True)),
        "acceptance_rate": round(total_likes / total_swipes, 2) if total_swipes > 0 else 0,
        "total_swipes": total_swipes,
        "total_likes": total_likes,
        "total_skips": total_skips
    }


def get_feedback_prompt_section() -> str:
    """
    Generate prompt section based on swipe feedback.

    Returns a string to inject into AI prompts.
    """
    patterns = get_swipe_patterns()

    if patterns['total_swipes'] < 10:
        return ""  # Not enough data yet

    lines = ["\n### LEARNED FROM YOUR SWIPES"]
    lines.append(f"(Based on {patterns['total_swipes']} swipes, {patterns['acceptance_rate']*100:.0f}% acceptance rate)")

    # Top liked genres
    liked = patterns.get('liked_genres', {})
    if liked:
        top_liked = list(liked.items())[:4]
        if top_liked:
            genre_str = ', '.join([f"{g} ({int(r*100)}%)" for g, r in top_liked])
            lines.append(f"\n**You tend to LIKE**: {genre_str}")

    # Skipped genres (high skip rate)
    skipped = patterns.get('skipped_genres', {})
    if skipped:
        top_skipped = list(skipped.items())[:3]
        if top_skipped:
            skip_str = ', '.join([f"{g} ({int(r*100)}% skip)" for g, r in top_skipped])
            lines.append(f"**You often SKIP**: {skip_str}")

    # Decade preference
    decades = patterns.get('liked_decades', {})
    if decades:
        top_decade = list(decades.items())[0] if decades else None
        if top_decade and top_decade[1] > 0.5:
            lines.append(f"**Preferred era**: {top_decade[0]} films ({int(top_decade[1]*100)}% acceptance)")

    # Best performing source
    sources = patterns.get('liked_sources', {})
    if sources:
        best_source = list(sources.items())[0] if sources else None
        if best_source:
            lines.append(f"**Best source accuracy**: {best_source[0]} ({int(best_source[1]*100)}% acceptance)")

    # Actionable insight
    if patterns['acceptance_rate'] < 0.3:
        lines.append("\n→ Low acceptance rate suggests recommendations need better personalization")
    elif patterns['acceptance_rate'] > 0.5:
        lines.append("\n→ High acceptance rate - recommendations are well-matched!")

    return '\n'.join(lines)


def get_genre_boost_weights() -> Dict[str, float]:
    """
    Get genre weights for boosting/reducing recommendations.

    Returns dict of genre -> weight multiplier.
    - > 1.0 = boost this genre
    - < 1.0 = reduce this genre
    """
    patterns = get_swipe_patterns()

    if patterns['total_swipes'] < 10:
        return {}  # Not enough data

    weights = {}

    # Boost genres with high acceptance
    for genre, rate in patterns.get('liked_genres', {}).items():
        if rate > 0.6:
            weights[genre] = 1.0 + (rate - 0.5)  # 1.1 to 1.5 boost

    # Reduce genres with high skip rate
    for genre, rate in patterns.get('skipped_genres', {}).items():
        if rate > 0.6:
            weights[genre] = 1.0 - (rate - 0.5)  # 0.5 to 0.9 reduction

    return weights


def should_regenerate_recommendations() -> bool:
    """
    Check if we have enough swipe data to regenerate with feedback.

    Returns True if we have 10+ swipes and should incorporate feedback.
    """
    patterns = get_swipe_patterns()
    return patterns['total_swipes'] >= 10


def get_swipe_summary() -> str:
    """
    Get a human-readable summary of swipe patterns.
    """
    patterns = get_swipe_patterns()

    if patterns['total_swipes'] == 0:
        return "No swipes yet. Start swiping to teach me your preferences!"

    lines = [
        f"📊 Swipe Summary ({patterns['total_swipes']} total)",
        f"   ✅ Liked: {patterns['total_likes']} ({patterns['acceptance_rate']*100:.0f}%)",
        f"   ❌ Skipped: {patterns['total_skips']}"
    ]

    if patterns.get('liked_genres'):
        top_genre = list(patterns['liked_genres'].items())[0]
        lines.append(f"   🎬 Top genre: {top_genre[0]} ({int(top_genre[1]*100)}% acceptance)")

    if patterns.get('skipped_genres'):
        skip_genre = list(patterns['skipped_genres'].items())[0]
        lines.append(f"   ⏭️  Often skip: {skip_genre[0]}")

    return '\n'.join(lines)


if __name__ == '__main__':
    print("=" * 60)
    print("SWIPE ANALYTICS")
    print("=" * 60)

    patterns = get_swipe_patterns()

    if patterns['total_swipes'] == 0:
        print("\nNo swipe data yet. Swipe through some recommendations first!")
    else:
        print(f"\nTotal swipes: {patterns['total_swipes']}")
        print(f"Acceptance rate: {patterns['acceptance_rate']*100:.0f}%")
        print(f"Likes: {patterns['total_likes']} | Skips: {patterns['total_skips']}")

        print("\n📈 Liked Genres:")
        for genre, rate in list(patterns.get('liked_genres', {}).items())[:5]:
            print(f"   {genre}: {int(rate*100)}% acceptance")

        print("\n📉 Skipped Genres:")
        for genre, rate in list(patterns.get('skipped_genres', {}).items())[:5]:
            print(f"   {genre}: {int(rate*100)}% skip rate")

        print("\n📅 Decade Preferences:")
        for decade, rate in list(patterns.get('liked_decades', {}).items())[:4]:
            print(f"   {decade}: {int(rate*100)}% acceptance")

        print("\n🤖 Source Accuracy:")
        for source, rate in patterns.get('liked_sources', {}).items():
            print(f"   {source}: {int(rate*100)}% acceptance")

        print("\n" + "=" * 60)
        print("PROMPT SECTION:")
        print("=" * 60)
        print(get_feedback_prompt_section())
