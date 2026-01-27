"""
AI Ensemble: Claude + ChatGPT + Gemini with web search.

Each model independently recommends movies based on Letterboxd ratings.
Uses enhanced taste profiles for better personalization.
Requires API keys in .env file.
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from taste_analyzer import build_taste_profile, format_taste_profile_for_prompt
from swipe_analytics import get_feedback_prompt_section
from database import get_all_friends, get_all_ratings, get_watched_movie_ids

load_dotenv()

# API clients
import anthropic
import openai
from google import genai

# Initialize clients
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_KEY = os.getenv('GOOGLE_API_KEY')

if ANTHROPIC_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

if OPENAI_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_KEY)

if GOOGLE_KEY:
    # Use new Google GenAI SDK for Gemini 3
    gemini_client = genai.Client(api_key=GOOGLE_KEY)
else:
    gemini_client = None


def format_ratings_for_prompt(ratings: List[Dict[str, Any]]) -> str:
    """Format Letterboxd ratings for AI prompt."""
    if not ratings:
        return "No ratings provided."

    # Group by rating score
    by_rating = {}
    for r in ratings:
        score = r['rating']
        if score not in by_rating:
            by_rating[score] = []
        by_rating[score].append(r)

    lines = []
    for score in sorted(by_rating.keys(), reverse=True):
        movies = by_rating[score]
        lines.append(f"\n{score}★:")
        for m in movies[:15]:  # Limit to 15 per rating
            genres_str = ', '.join(m.get('genres', [])[:3])
            lines.append(f"  - {m['title']} ({m.get('year', 'N/A')}) [{genres_str}]")

    return '\n'.join(lines)


def get_friend_recommendations_context(min_compatibility: float = 50.0, max_friends: int = 5) -> str:
    """
    Get friend recommendations context for AI prompts.

    Finds movies that highly compatible friends loved but user hasn't seen.

    Args:
        min_compatibility: Minimum compatibility score (0-100)
        max_friends: Maximum number of friends to include

    Returns:
        Formatted string for AI prompt, e.g.:
        "### FRIEND RECOMMENDATIONS
         Alice (78% match) loves: Movie1 (4.5★), Movie2 (5★)
         Bob (65% match) loves: Movie3 (5★)"
    """
    friends = get_all_friends()

    if not friends:
        return ""

    # Filter by compatibility and limit
    compatible_friends = [
        f for f in friends
        if f.get('compatibility_score') and f['compatibility_score'] >= min_compatibility
    ][:max_friends]

    if not compatible_friends:
        return ""

    # Get user's watched movie IDs
    watched_ids = set(get_watched_movie_ids())

    lines = ["### FRIEND RECOMMENDATIONS"]
    lines.append("These are movies your friends with similar taste loved:\n")

    for friend in compatible_friends:
        friend_name = friend['name']
        friend_username = friend.get('letterboxd_username', friend_name)
        compatibility = friend['compatibility_score']

        # Get friend's high-rated movies
        friend_ratings = get_all_ratings(user=friend_username)

        # Filter to 4+ star ratings that user hasn't seen
        friend_favorites = [
            r for r in friend_ratings
            if r['rating'] >= 4.0 and r.get('tmdb_id') not in watched_ids
        ][:5]  # Top 5 favorites

        if friend_favorites:
            movies_str = ', '.join([
                f"{r['title']} ({r['rating']}★)"
                for r in friend_favorites
            ])
            lines.append(f"**{friend_name}** ({compatibility:.0f}% match) loves: {movies_str}")

    if len(lines) <= 2:  # Only header, no actual recommendations
        return ""

    lines.append("\n→ Consider recommending these friend-endorsed movies!")

    return '\n'.join(lines)


def build_enhanced_prompt(ratings: List[Dict[str, Any]], count: int, friend_context: str = "") -> str:
    """
    Build enhanced prompt with full taste profile and swipe feedback.
    """
    # Build taste profile
    profile = build_taste_profile(ratings)
    taste_text = format_taste_profile_for_prompt(profile)

    # Get swipe feedback (if enough data)
    feedback_text = get_feedback_prompt_section()

    # Get anti-preferences for explicit avoidance
    anti = profile.get('anti_preferences', {})
    disliked_genres = anti.get('disliked_genres', [])
    avoid_text = f"AVOID these genres/types: {', '.join(disliked_genres)}" if disliked_genres else ""

    prompt = f"""## YOUR TASTE PROFILE

{taste_text}

{feedback_text}

{friend_context}

---

## RECOMMENDATION REQUEST

Recommend {count} movies I haven't seen that match my taste profile.

### CRITICAL REQUIREMENTS:
1. **RECENCY**: At least 40% of recommendations must be from 2024-2025 (recent releases)
2. **GENRE DIVERSITY**: Include variety across Action, Comedy, Drama, Sci-Fi, Horror, Romance
3. **PERSONALIZATION**: Reference specific movies from my profile in your reasoning
{f"4. **{avoid_text}**" if avoid_text else ""}

### For each movie provide:
- Title (Year)
- Personalized reasoning that references my specific favorites or patterns
- Streaming availability if known

### REASONING QUALITY:
Good: "Like Whiplash, this features an intense mentor relationship and jazz music themes"
Bad: "You'll enjoy this drama"

Format as JSON array:
[
  {{
    "title": "Movie Title",
    "year": 2024,
    "reasoning": "Specific reason referencing your taste...",
    "streaming": "Netflix"
  }}
]

Return only the JSON array."""

    return prompt


def get_claude_recommendations(ratings: List[Dict[str, Any]], count: int = 15, friend_context: str = "") -> List[Dict[str, Any]]:
    """
    Get movie recommendations from Claude Opus 4.5 with enhanced taste profile.
    """
    if not ANTHROPIC_KEY:
        print("⚠️  Skipping Claude: ANTHROPIC_API_KEY not set")
        return []

    print("🤖 Getting recommendations from Claude Opus 4.5...")

    prompt = build_enhanced_prompt(ratings, count, friend_context)

    try:
        # Use Claude Opus 4.5 (released Nov 2025) for best quality recommendations
        # Opus 4.5 has 80.9% on SWE-bench Verified and excellent reasoning
        response = anthropic_client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        content = response.content[0].text
        # Find JSON in response
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            recommendations = json.loads(json_str)
            print(f"   ✓ Got {len(recommendations)} recommendations from Claude")
            return recommendations
        else:
            print(f"   ⚠️  Could not parse Claude response as JSON")
            return []

    except Exception as e:
        print(f"   ❌ Claude error: {e}")
        return []


def get_chatgpt_recommendations(ratings: List[Dict[str, Any]], count: int = 15, friend_context: str = "") -> List[Dict[str, Any]]:
    """
    Get movie recommendations from ChatGPT with enhanced taste profile.
    """
    if not OPENAI_KEY:
        print("⚠️  Skipping ChatGPT: OPENAI_API_KEY not set")
        return []

    print("🤖 Getting recommendations from ChatGPT...")

    prompt = build_enhanced_prompt(ratings, count, friend_context)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a movie recommendation expert. Analyze user preferences and suggest films they'll love."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content
        # Parse JSON
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            recommendations = json.loads(json_str)
            print(f"   ✓ Got {len(recommendations)} recommendations from ChatGPT")
            return recommendations
        else:
            print(f"   ⚠️  Could not parse ChatGPT response as JSON")
            return []

    except Exception as e:
        print(f"   ❌ ChatGPT error: {e}")
        return []


def get_gemini_recommendations(ratings: List[Dict[str, Any]], count: int = 15, friend_context: str = "") -> List[Dict[str, Any]]:
    """
    Get movie recommendations from Gemini 3 Pro with Google Search grounding and enhanced taste profile.
    """
    if not GOOGLE_KEY:
        print("⚠️  Skipping Gemini: GOOGLE_API_KEY not set")
        return []

    print("🤖 Getting recommendations from Gemini 3 Pro (with Google Search)...")

    prompt = build_enhanced_prompt(ratings, count, friend_context)

    try:
        # Use new Google GenAI client with search grounding
        response = gemini_client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "tools": [{"google_search": {}}]  # Enable Google Search grounding
            }
        )
        content = response.text

        # Parse JSON
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            recommendations = json.loads(json_str)
            print(f"   ✓ Got {len(recommendations)} recommendations from Gemini")
            return recommendations
        else:
            print(f"   ⚠️  Could not parse Gemini response as JSON")
            return []

    except Exception as e:
        print(f"   ❌ Gemini error: {e}")
        return []


def get_all_ai_recommendations(ratings: List[Dict[str, Any]], count_per_model: int = 15, friend_context: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get recommendations from all available AI models with enhanced taste profiles.

    Runs all AI model calls in PARALLEL for maximum speed.

    Args:
        ratings: User's movie ratings
        count_per_model: Number of recommendations per AI model
        friend_context: Optional friend recommendation context. If None, will auto-generate.

    Returns:
        {
            'claude': [...],
            'chatgpt': [...],  (only if OpenAI key is set)
            'gemini': [...]
        }
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    start_time = time.time()
    print("\n🎬 Generating AI recommendations with enhanced taste profile...\n")
    print("⚡ Running AI models in PARALLEL for faster results\n")

    # Auto-generate friend context if not provided
    if friend_context is None:
        friend_context = get_friend_recommendations_context()
        if friend_context:
            print("👥 Including friend recommendations in prompts\n")

    # Ensure friend_context is a string
    friend_context = friend_context or ""

    results = {
        'claude': [],
        'chatgpt': [],
        'gemini': []
    }

    # Define tasks to run in parallel
    tasks = [
        ('claude', get_claude_recommendations, ratings, count_per_model, friend_context),
        ('gemini', get_gemini_recommendations, ratings, count_per_model, friend_context),
    ]

    # Only add ChatGPT if OpenAI key is available
    if OPENAI_KEY:
        tasks.append(('chatgpt', get_chatgpt_recommendations, ratings, count_per_model, friend_context))
    else:
        print("⚠️  OpenAI API key not set, skipping ChatGPT (Claude and Gemini only)")

    # Run all AI calls in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_model = {
            executor.submit(func, r, c, f): model_name
            for model_name, func, r, c, f in tasks
        }

        for future in as_completed(future_to_model):
            model_name = future_to_model[future]
            try:
                results[model_name] = future.result()
            except Exception as e:
                print(f"   ❌ {model_name} failed: {e}")
                results[model_name] = []

    elapsed = time.time() - start_time
    total = sum(len(v) for v in results.values())
    active_models = sum(1 for v in results.values() if v)
    print(f"\n✅ Total AI recommendations: {total} from {active_models} models in {elapsed:.1f}s")
    print(f"   Claude: {len(results['claude'])}")
    print(f"   ChatGPT: {len(results['chatgpt'])}")
    print(f"   Gemini: {len(results['gemini'])}")

    return results


if __name__ == '__main__':
    # Test with sample ratings
    print("Testing AI ensemble...")

    sample_ratings = [
        {'title': 'Blade Runner 2049', 'year': 2017, 'rating': 5.0, 'genres': ['Sci-Fi', 'Thriller']},
        {'title': 'The Matrix', 'year': 1999, 'rating': 5.0, 'genres': ['Sci-Fi', 'Action']},
        {'title': 'Inception', 'year': 2010, 'rating': 4.5, 'genres': ['Sci-Fi', 'Thriller']},
        {'title': 'Interstellar', 'year': 2014, 'rating': 4.5, 'genres': ['Sci-Fi', 'Drama']},
        {'title': 'Dune', 'year': 2021, 'rating': 4.0, 'genres': ['Sci-Fi', 'Adventure']},
    ]

    results = get_all_ai_recommendations(sample_ratings, count_per_model=5)

    print("\n📋 Sample recommendations:")
    for source, recs in results.items():
        if recs:
            print(f"\n{source.upper()}:")
            for rec in recs[:3]:
                print(f"  - {rec.get('title')} ({rec.get('year')})")
                print(f"    {rec.get('reasoning')}")
