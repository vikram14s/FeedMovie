"""
TMDB API client for movie metadata and streaming availability.

Requires TMDB_API_KEY in .env file.
Get your free API key at: https://www.themoviedb.org/settings/api
"""

import os
import requests
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from diskcache import Cache

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'

# Simple disk cache to avoid rate limits
cache = Cache('data/cache')


def search_movie(title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Search for a movie by title and year, return enriched data.

    Returns:
        Dict with: tmdb_id, title, year, genres, poster_path,
                  streaming_providers, overview
        None if not found
    """
    if not TMDB_API_KEY:
        raise ValueError("TMDB_API_KEY not set in .env file")

    # Check cache first
    cache_key = f"search:{title}:{year}"
    if cache_key in cache:
        return cache[cache_key]

    # Search for movie
    time.sleep(0.25)  # Rate limiting: 40 requests/10 seconds = 1 per 0.25s
    params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'page': 1
    }
    if year:
        params['year'] = year
        params['primary_release_year'] = year

    try:
        response = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params)
        response.raise_for_status()
        data = response.json()

        if not data['results']:
            cache[cache_key] = None
            return None

        # Get first result (best match)
        movie = data['results'][0]
        tmdb_id = movie['id']

        # Fetch detailed info + streaming providers
        movie_data = get_movie_details(tmdb_id)

        # Cache and return
        cache[cache_key] = movie_data
        return movie_data

    except requests.RequestException as e:
        print(f"Error searching for '{title}': {e}")
        return None


def search_movies(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for movies by query, return list of results with basic info.

    Returns:
        List of dicts with: tmdb_id, title, year, poster_path, overview, genres
    """
    if not TMDB_API_KEY:
        raise ValueError("TMDB_API_KEY not set in .env file")

    cache_key = f"search_multi:{query}:{limit}"
    if cache_key in cache:
        return cache[cache_key]

    time.sleep(0.25)  # Rate limiting

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={
                'api_key': TMDB_API_KEY,
                'query': query,
                'page': 1
            }
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for movie in data['results'][:limit]:
            results.append({
                'tmdb_id': movie['id'],
                'title': movie['title'],
                'year': int(movie['release_date'][:4]) if movie.get('release_date') else None,
                'poster_path': f"{IMAGE_BASE_URL}{movie['poster_path']}" if movie.get('poster_path') else None,
                'overview': movie.get('overview', ''),
                'genre_ids': movie.get('genre_ids', [])
            })

        # Cache for 1 hour
        cache.set(cache_key, results, expire=3600)
        return results

    except requests.RequestException as e:
        print(f"Error searching for '{query}': {e}")
        return []


def get_movie_details(tmdb_id: int) -> Dict[str, Any]:
    """
    Get detailed movie information including streaming providers.
    """
    # Check cache
    cache_key = f"movie:{tmdb_id}"
    if cache_key in cache:
        return cache[cache_key]

    time.sleep(0.25)  # Rate limiting

    try:
        # Get movie details
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            params={'api_key': TMDB_API_KEY}
        )
        response.raise_for_status()
        movie = response.json()

        # Get streaming providers
        streaming_response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/watch/providers",
            params={'api_key': TMDB_API_KEY}
        )
        streaming_response.raise_for_status()
        streaming_data = streaming_response.json()

        # Parse streaming providers (US region by default)
        us_providers = streaming_data.get('results', {}).get('US', {})
        streaming_providers = parse_streaming_providers(us_providers)

        # Get external IDs (including IMDB)
        external_ids_response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/external_ids",
            params={'api_key': TMDB_API_KEY}
        )
        external_ids_response.raise_for_status()
        external_ids = external_ids_response.json()
        imdb_id = external_ids.get('imdb_id')

        # Get IMDb and Rotten Tomatoes ratings + awards from OMDB
        imdb_rating = None
        rt_rating = None
        awards = None
        if imdb_id:
            from omdb_client import get_ratings_by_imdb_id
            omdb_data = get_ratings_by_imdb_id(imdb_id)
            if omdb_data:
                imdb_rating = float(omdb_data['imdb_rating']) if omdb_data.get('imdb_rating') else None
                rt_rating = omdb_data.get('rt_rating')  # e.g., "94%"
                awards = omdb_data.get('awards')  # e.g., "Won 2 Oscars. 50 wins & 123 nominations"

        # Get credits (director, cast)
        credits = get_movie_credits(tmdb_id)

        # Build result
        result = {
            'tmdb_id': tmdb_id,
            'imdb_id': imdb_id,
            'title': movie['title'],
            'year': int(movie['release_date'][:4]) if movie.get('release_date') else None,
            'genres': [g['name'] for g in movie.get('genres', [])],
            'poster_path': f"{IMAGE_BASE_URL}{movie['poster_path']}" if movie.get('poster_path') else None,
            'streaming_providers': streaming_providers,
            'overview': movie.get('overview', ''),
            'tmdb_rating': round(movie.get('vote_average', 0), 1),
            'tmdb_vote_count': movie.get('vote_count', 0),
            'imdb_rating': imdb_rating,
            'rt_rating': rt_rating,
            'directors': credits.get('directors', []),
            'cast': credits.get('cast', []),
            'awards': awards
        }

        # Cache and return
        cache.set(cache_key, result, expire=2592000)  # 30 days
        return result

    except requests.RequestException as e:
        print(f"Error getting details for TMDB ID {tmdb_id}: {e}")
        # Return minimal data on error
        return {
            'tmdb_id': tmdb_id,
            'title': 'Unknown',
            'year': None,
            'genres': [],
            'poster_path': None,
            'streaming_providers': {},
            'overview': ''
        }


def get_movie_keywords(tmdb_id: int) -> List[str]:
    """
    Get keywords/themes for a movie from TMDB.

    Returns list of keyword strings like:
    ["time travel", "heist", "artificial intelligence", "dystopia"]
    """
    cache_key = f"keywords:{tmdb_id}"
    if cache_key in cache:
        return cache[cache_key]

    time.sleep(0.25)  # Rate limiting

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/keywords",
            params={'api_key': TMDB_API_KEY}
        )
        response.raise_for_status()
        data = response.json()

        keywords = [k['name'] for k in data.get('keywords', [])]

        # Cache for 30 days
        cache.set(cache_key, keywords, expire=2592000)
        return keywords

    except requests.RequestException as e:
        print(f"Error getting keywords for TMDB ID {tmdb_id}: {e}")
        return []


def get_movie_credits(tmdb_id: int) -> Dict[str, List[str]]:
    """
    Get director and top cast for a movie.

    Returns:
        {
            "directors": ["Christopher Nolan"],
            "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", ...]
        }
    """
    cache_key = f"credits:{tmdb_id}"
    if cache_key in cache:
        return cache[cache_key]

    time.sleep(0.25)  # Rate limiting

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            params={'api_key': TMDB_API_KEY}
        )
        response.raise_for_status()
        data = response.json()

        # Get directors from crew
        directors = [
            c['name'] for c in data.get('crew', [])
            if c.get('job') == 'Director'
        ]

        # Get top 5 cast members
        cast = [
            c['name'] for c in data.get('cast', [])[:5]
        ]

        result = {
            "directors": directors,
            "cast": cast
        }

        cache.set(cache_key, result, expire=2592000)  # 30 days
        return result

    except requests.RequestException as e:
        print(f"Error getting credits for TMDB ID {tmdb_id}: {e}")
        return {"directors": [], "cast": []}


def parse_streaming_providers(us_providers: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse TMDB streaming provider data into simple format with logos.

    Returns:
        {
            'subscription': [{'name': 'Netflix', 'logo': 'https://...'}],
            'rent': [{'name': 'Apple TV', 'logo': 'https://...'}],
            'buy': [{'name': 'Apple TV', 'logo': 'https://...'}]
        }
    """
    result = {
        'subscription': [],
        'rent': [],
        'buy': []
    }

    TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/original'

    # Subscription streaming (flatrate)
    if 'flatrate' in us_providers:
        result['subscription'] = [
            {
                'name': p['provider_name'],
                'logo': f"{TMDB_IMAGE_BASE}{p['logo_path']}" if p.get('logo_path') else None
            }
            for p in us_providers['flatrate']
        ]

    # Rental options
    if 'rent' in us_providers:
        result['rent'] = [
            {
                'name': p['provider_name'],
                'logo': f"{TMDB_IMAGE_BASE}{p['logo_path']}" if p.get('logo_path') else None
            }
            for p in us_providers['rent']
        ]

    # Purchase options
    if 'buy' in us_providers:
        result['buy'] = [
            {
                'name': p['provider_name'],
                'logo': f"{TMDB_IMAGE_BASE}{p['logo_path']}" if p.get('logo_path') else None
            }
            for p in us_providers['buy']
        ]

    return result


def get_popular_movies(page: int = 1) -> List[Dict[str, Any]]:
    """
    Get popular movies from TMDB (for testing).
    """
    if not TMDB_API_KEY:
        raise ValueError("TMDB_API_KEY not set in .env file")

    cache_key = f"popular:page{page}"
    if cache_key in cache:
        return cache[cache_key]

    time.sleep(0.25)  # Rate limiting

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/popular",
            params={'api_key': TMDB_API_KEY, 'page': page}
        )
        response.raise_for_status()
        data = response.json()

        movies = []
        for movie in data['results'][:10]:  # Limit to 10
            movie_data = get_movie_details(movie['id'])
            movies.append(movie_data)

        cache.set(cache_key, movies, expire=86400)  # 1 day
        return movies

    except requests.RequestException as e:
        print(f"Error getting popular movies: {e}")
        return []


if __name__ == '__main__':
    # Test the API
    print("Testing TMDB API...")

    # Test search
    print("\n1. Searching for 'Blade Runner' (1982)...")
    result = search_movie('Blade Runner', 1982)
    if result:
        print(f"   Found: {result['title']} ({result['year']})")
        print(f"   Genres: {', '.join(result['genres'])}")
        print(f"   Streaming: {result['streaming_providers']}")
    else:
        print("   Not found")

    # Test search without year
    print("\n2. Searching for 'The Matrix'...")
    result = search_movie('The Matrix')
    if result:
        print(f"   Found: {result['title']} ({result['year']})")
        print(f"   Streaming: {result['streaming_providers']}")

    print("\n✅ TMDB client test complete!")
