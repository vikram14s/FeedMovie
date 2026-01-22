"""
Scrape Friends CLI - Import Letterboxd friends and calculate compatibility.

Usage:
    uv run backend/scrape_friends.py <username>
    uv run backend/scrape_friends.py vikram14s

This script:
1. Scrapes the /following/ page to get friend list
2. Imports each friend's ratings into the database
3. Calculates Pearson correlation compatibility scores
4. Stores friends with compatibility scores
"""

import sys
import asyncio
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import math

from letterboxd_scraper import scrape_following_page, scrape_user_ratings
from database import (
    get_connection, add_friend, update_friend_compatibility,
    get_all_ratings, add_movie, add_rating
)
from tmdb_client import search_movie


def calculate_pearson_correlation(
    user_ratings: Dict[str, float],
    friend_ratings: Dict[str, float]
) -> Tuple[float, int]:
    """
    Calculate Pearson correlation coefficient between two users' ratings.

    Args:
        user_ratings: Dict of {movie_title_year: rating} for main user
        friend_ratings: Dict of {movie_title_year: rating} for friend

    Returns:
        (correlation, overlap_count) - correlation is -1 to 1, overlap is # shared movies
    """
    # Find movies both have rated
    common_movies = set(user_ratings.keys()) & set(friend_ratings.keys())
    n = len(common_movies)

    if n < 3:  # Need at least 3 movies for meaningful correlation
        return 0.0, n

    # Calculate means
    user_sum = sum(user_ratings[m] for m in common_movies)
    friend_sum = sum(friend_ratings[m] for m in common_movies)
    user_mean = user_sum / n
    friend_mean = friend_sum / n

    # Calculate Pearson correlation
    numerator = 0.0
    user_sq_sum = 0.0
    friend_sq_sum = 0.0

    for movie in common_movies:
        user_diff = user_ratings[movie] - user_mean
        friend_diff = friend_ratings[movie] - friend_mean
        numerator += user_diff * friend_diff
        user_sq_sum += user_diff ** 2
        friend_sq_sum += friend_diff ** 2

    denominator = math.sqrt(user_sq_sum * friend_sq_sum)

    if denominator == 0:
        return 0.0, n

    correlation = numerator / denominator
    return correlation, n


def normalize_movie_key(title: str, year: int) -> str:
    """Create normalized key for movie comparison."""
    # Lowercase, remove special chars for better matching
    clean_title = ''.join(c.lower() for c in title if c.isalnum() or c == ' ')
    clean_title = ' '.join(clean_title.split())  # Normalize whitespace
    return f"{clean_title}_{year}" if year else clean_title


async def import_friends(username: str, max_friends: int = 20, ratings_per_friend: int = 50):
    """
    Import friends from Letterboxd and calculate compatibility scores.

    Args:
        username: Letterboxd username to import friends from
        max_friends: Maximum number of friends to import
        ratings_per_friend: Number of ratings to fetch per friend
    """
    print(f"\n{'='*60}")
    print(f"IMPORTING FRIENDS FOR: {username}")
    print(f"{'='*60}")

    # Step 1: Get user's own ratings for correlation calculation
    print(f"\n1. Loading your ratings...")
    user_ratings_list = get_all_ratings(username)

    if not user_ratings_list:
        print(f"   No ratings found for {username} in database.")
        print(f"   Please import your Letterboxd data first.")
        return

    # Convert to dict for correlation
    user_ratings_dict = {}
    for r in user_ratings_list:
        key = normalize_movie_key(r['title'], r.get('year'))
        user_ratings_dict[key] = r['rating']

    print(f"   Found {len(user_ratings_dict)} of your ratings")

    # Step 2: Scrape following page
    print(f"\n2. Scraping your following list...")
    friends = await scrape_following_page(username, max_pages=3)

    if not friends:
        print(f"   No friends found on {username}'s following page.")
        print(f"   Make sure the account exists and has public following list.")
        return

    print(f"   Found {len(friends)} friends")

    # Limit friends
    friends = friends[:max_friends]
    print(f"   Processing top {len(friends)} friends...")

    # Step 3: Process each friend
    results = []

    for i, friend in enumerate(friends, 1):
        friend_username = friend['username']
        display_name = friend.get('display_name', friend_username)

        print(f"\n   [{i}/{len(friends)}] Processing @{friend_username}...")

        try:
            # Scrape friend's ratings
            friend_ratings = await scrape_user_ratings(friend_username, limit=ratings_per_friend)

            if not friend_ratings:
                print(f"      No ratings found, skipping")
                continue

            print(f"      Found {len(friend_ratings)} ratings")

            # Convert to dict for correlation
            friend_ratings_dict = {}
            for r in friend_ratings:
                key = normalize_movie_key(r['title'], r.get('year'))
                friend_ratings_dict[key] = r['rating']

            # Calculate compatibility
            correlation, overlap = calculate_pearson_correlation(
                user_ratings_dict, friend_ratings_dict
            )

            # Convert correlation to 0-100% compatibility score
            # Pearson is -1 to 1, we convert to 0% to 100%
            compatibility = (correlation + 1) / 2 * 100

            print(f"      Overlap: {overlap} movies | Compatibility: {compatibility:.1f}%")

            # Save friend to database
            add_friend(display_name, friend_username)
            update_friend_compatibility(display_name, compatibility)

            # Save friend's ratings to database (for future recommendations)
            movies_added = 0
            for r in friend_ratings[:30]:  # Store top 30 ratings per friend
                # Try to find movie in TMDB
                tmdb_result = search_movie(r['title'], r.get('year'))
                if tmdb_result:
                    movie_id = add_movie(
                        tmdb_id=tmdb_result['tmdb_id'],
                        title=tmdb_result['title'],
                        year=tmdb_result['year'],
                        genres=tmdb_result.get('genres', []),
                        poster_path=tmdb_result.get('poster_path'),
                        streaming_providers=tmdb_result.get('streaming_providers', {}),
                        overview=tmdb_result.get('overview', '')
                    )
                    # Add rating with friend's username
                    add_rating(movie_id, r['rating'], user=friend_username)
                    movies_added += 1

            print(f"      Saved {movies_added} ratings to database")

            results.append({
                'username': friend_username,
                'display_name': display_name,
                'compatibility': compatibility,
                'overlap': overlap,
                'ratings_count': len(friend_ratings)
            })

            # Rate limiting
            await asyncio.sleep(1)

        except Exception as e:
            print(f"      Error: {e}")
            continue

    # Step 4: Summary
    print(f"\n{'='*60}")
    print("IMPORT COMPLETE")
    print(f"{'='*60}")

    if results:
        # Sort by compatibility
        results.sort(key=lambda x: x['compatibility'], reverse=True)

        print(f"\nTop compatible friends:")
        for r in results[:10]:
            emoji = "🔥" if r['compatibility'] >= 70 else "👍" if r['compatibility'] >= 50 else "👋"
            print(f"   {emoji} {r['display_name']} (@{r['username']})")
            print(f"      {r['compatibility']:.1f}% match | {r['overlap']} shared movies")

        high_match = sum(1 for r in results if r['compatibility'] >= 70)
        medium_match = sum(1 for r in results if 50 <= r['compatibility'] < 70)

        print(f"\nSummary:")
        print(f"   Total friends imported: {len(results)}")
        print(f"   High compatibility (70%+): {high_match}")
        print(f"   Medium compatibility (50-70%): {medium_match}")
    else:
        print("\nNo friends could be processed.")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run backend/scrape_friends.py <username>")
        print("Example: uv run backend/scrape_friends.py vikram14s")
        sys.exit(1)

    username = sys.argv[1]

    # Optional: max friends
    max_friends = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    print(f"\n🔍 Starting friend import for @{username}...")
    print(f"   Max friends: {max_friends}")

    asyncio.run(import_friends(username, max_friends=max_friends))

    print("\n✅ Friend import complete!")
    print("   Run recommendations again to include friend suggestions.")


if __name__ == '__main__':
    main()
