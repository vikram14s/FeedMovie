"""
AI Ensemble: Claude + ChatGPT + Gemini with web search.

Each model independently recommends movies based on Letterboxd ratings.
Requires API keys in .env file.
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

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


def get_claude_recommendations(ratings: List[Dict[str, Any]], count: int = 15) -> List[Dict[str, Any]]:
    """
    Get movie recommendations from Claude Opus 4.5.
    """
    if not ANTHROPIC_KEY:
        print("⚠️  Skipping Claude: ANTHROPIC_API_KEY not set")
        return []

    print("🤖 Getting recommendations from Claude Opus 4.5...")

    ratings_text = format_ratings_for_prompt(ratings)
    top_movies = [r['title'] for r in sorted(ratings, key=lambda x: x['rating'], reverse=True)[:10]]
    top_movies_str = ', '.join(top_movies)

    prompt = f"""Based on these Letterboxd ratings:
{ratings_text}

My top favorites: {top_movies_str}

Please recommend {count} movies I haven't seen that I would likely enjoy.

IMPORTANT: Ensure GENRE DIVERSITY - include at least 3-4 movies from EACH of these genres:
- Action (including thrillers with action)
- Comedy (including dark comedy, romantic comedy)
- Drama (character-driven stories)
- Sci-Fi/Fantasy
- Horror/Thriller
- Romance

Consider:
1. Recent acclaimed films (2020-2025) in similar genres
2. Hidden gems and cult classics that match my taste
3. Movies from different eras that share themes with my favorites
4. International cinema that fits my preferences

For each movie, provide:
- Title (Year)
- One sentence explaining why I'd like it based on my rating patterns
- Streaming availability if known (e.g., "Netflix", "Prime Video", "Max")

Focus on quality recommendations that truly match my taste profile, but PRIORITIZE GENRE DIVERSITY.

Format as JSON array:
[
  {{
    "title": "Movie Title",
    "year": 2023,
    "reasoning": "You'll love this because...",
    "streaming": "Netflix, Prime Video"
  }}
]

Return only the JSON array, no other text."""

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


def get_chatgpt_recommendations(ratings: List[Dict[str, Any]], count: int = 15) -> List[Dict[str, Any]]:
    """
    Get movie recommendations from ChatGPT.
    """
    if not OPENAI_KEY:
        print("⚠️  Skipping ChatGPT: OPENAI_API_KEY not set")
        return []

    print("🤖 Getting recommendations from ChatGPT...")

    ratings_text = format_ratings_for_prompt(ratings)
    top_movies = [r['title'] for r in sorted(ratings, key=lambda x: x['rating'], reverse=True)[:10]]
    top_movies_str = ', '.join(top_movies)

    prompt = f"""Based on these Letterboxd ratings:
{ratings_text}

My top favorites: {top_movies_str}

Please recommend {count} movies I haven't seen that I would likely enjoy.

IMPORTANT: Ensure GENRE DIVERSITY - include at least 3-4 movies from EACH of these genres:
- Action (including thrillers with action)
- Comedy (including dark comedy, romantic comedy)
- Drama (character-driven stories)
- Sci-Fi/Fantasy
- Horror/Thriller
- Romance

For each movie, provide:
- Title (Year)
- One sentence explaining why I'd like it
- Streaming availability if known

PRIORITIZE GENRE DIVERSITY while matching my taste.

Format as JSON array:
[
  {{
    "title": "Movie Title",
    "year": 2023,
    "reasoning": "You'll love this because...",
    "streaming": "Netflix, Prime Video"
  }}
]

Return only the JSON array."""

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


def get_gemini_recommendations(ratings: List[Dict[str, Any]], count: int = 15) -> List[Dict[str, Any]]:
    """
    Get movie recommendations from Gemini 3 Pro with Google Search grounding.
    """
    if not GOOGLE_KEY:
        print("⚠️  Skipping Gemini: GOOGLE_API_KEY not set")
        return []

    print("🤖 Getting recommendations from Gemini 3 Pro (with Google Search)...")

    ratings_text = format_ratings_for_prompt(ratings)
    top_movies = [r['title'] for r in sorted(ratings, key=lambda x: x['rating'], reverse=True)[:10]]
    top_movies_str = ', '.join(top_movies)

    prompt = f"""Based on these Letterboxd ratings:
{ratings_text}

My top favorites: {top_movies_str}

Please recommend {count} movies I haven't seen that I would likely enjoy.

IMPORTANT: Ensure GENRE DIVERSITY - include at least 3-4 movies from EACH of these genres:
- Action (including thrillers with action)
- Comedy (including dark comedy, romantic comedy)
- Drama (character-driven stories)
- Sci-Fi/Fantasy
- Horror/Thriller
- Romance

For each movie, provide:
- Title (Year)
- One sentence explaining why I'd like it
- Streaming availability if known

PRIORITIZE GENRE DIVERSITY while matching my taste.

Format as JSON array:
[
  {{
    "title": "Movie Title",
    "year": 2023,
    "reasoning": "You'll love this because...",
    "streaming": "Netflix, Prime Video"
  }}
]

Return only the JSON array."""

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


def get_all_ai_recommendations(ratings: List[Dict[str, Any]], count_per_model: int = 15) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get recommendations from all available AI models.

    Returns:
        {
            'claude': [...],
            'chatgpt': [...],  (only if OpenAI key is set)
            'gemini': [...]
        }
    """
    print("\n🎬 Generating AI recommendations...\n")

    results = {
        'claude': get_claude_recommendations(ratings, count_per_model),
        'gemini': get_gemini_recommendations(ratings, count_per_model)
    }

    # Only add ChatGPT if OpenAI key is available
    if OPENAI_KEY:
        results['chatgpt'] = get_chatgpt_recommendations(ratings, count_per_model)
    else:
        print("⚠️  OpenAI API key not set, skipping ChatGPT (Claude and Gemini only)")
        results['chatgpt'] = []

    total = sum(len(v) for v in results.values())
    active_models = sum(1 for v in results.values() if v)
    print(f"\n✅ Total AI recommendations: {total} from {active_models} models")
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
