"""
OMDB API client for fetching IMDb and Rotten Tomatoes ratings.

Get your free API key at: http://www.omdbapi.com/apikey.aspx
"""

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from diskcache import Cache

load_dotenv()

OMDB_API_KEY = os.getenv('OMDB_API_KEY')
OMDB_BASE_URL = 'http://www.omdbapi.com/'

# Shared cache with TMDB
cache = Cache('data/cache')


def get_ratings_by_imdb_id(imdb_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch ratings from OMDB using IMDb ID.

    Returns:
        {
            'imdb_rating': '8.5',
            'imdb_votes': '2.5M',
            'rt_rating': '94%',
            'metacritic_rating': '82'
        }
        None if not found or API key not set
    """
    if not OMDB_API_KEY or OMDB_API_KEY == 'your_omdb_api_key_here':
        return None

    if not imdb_id:
        return None

    # Check cache
    cache_key = f"omdb:{imdb_id}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        response = requests.get(
            OMDB_BASE_URL,
            params={
                'apikey': OMDB_API_KEY,
                'i': imdb_id,
                'plot': 'short'
            },
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if data.get('Response') == 'False':
            cache[cache_key] = None
            return None

        # Parse ratings and awards
        result = {
            'imdb_rating': None,
            'imdb_votes': None,
            'rt_rating': None,
            'metacritic_rating': None,
            'awards': None
        }

        # IMDb rating
        if data.get('imdbRating') and data['imdbRating'] != 'N/A':
            result['imdb_rating'] = data['imdbRating']

        if data.get('imdbVotes') and data['imdbVotes'] != 'N/A':
            result['imdb_votes'] = data['imdbVotes']

        # Rotten Tomatoes and Metacritic from Ratings array
        ratings_array = data.get('Ratings', [])
        for rating in ratings_array:
            source = rating.get('Source', '')
            value = rating.get('Value', '')

            if source == 'Rotten Tomatoes':
                result['rt_rating'] = value  # e.g., "94%"
            elif source == 'Metacritic':
                result['metacritic_rating'] = value.split('/')[0] if '/' in value else value

        # Awards (e.g., "Won 2 Oscars. 50 wins & 123 nominations total")
        if data.get('Awards') and data['Awards'] != 'N/A':
            result['awards'] = data['Awards']

        # Cache for 30 days
        cache.set(cache_key, result, expire=2592000)
        return result

    except Exception as e:
        print(f"Error fetching OMDB data for {imdb_id}: {e}")
        return None


if __name__ == '__main__':
    # Test with a known movie
    test_imdb_id = 'tt0111161'  # The Shawshank Redemption
    ratings = get_ratings_by_imdb_id(test_imdb_id)
    if ratings:
        print(f"Ratings for {test_imdb_id}:")
        print(f"  IMDb: {ratings['imdb_rating']} ({ratings['imdb_votes']} votes)")
        print(f"  Rotten Tomatoes: {ratings['rt_rating']}")
        print(f"  Metacritic: {ratings['metacritic_rating']}")
    else:
        print("OMDB API key not set or movie not found")
