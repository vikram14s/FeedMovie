"""
Import Letterboxd friends' ratings and calculate taste compatibility.

Usage:
    python backend/friends_import.py <friend_name> <path_to_ratings.csv>

Example:
    python backend/friends_import.py "Priya" data/letterboxd/priya_ratings.csv
"""

import csv
import sys
from scipy.stats import pearsonr
import numpy as np
from database import (add_friend, add_movie, add_rating, get_all_ratings,
                      update_friend_compatibility, get_movie_by_tmdb_id)
import tmdb_client


def import_friend_ratings(friend_name: str, csv_path: str):
    """Import a friend's Letterboxd ratings from CSV."""
    print(f"\n📚 Importing ratings for {friend_name}...")

    imported = 0
    skipped = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = row['Name']
            year = int(row['Year']) if row['Year'] else None
            rating = float(row['Rating'])
            watched_date = row['Date']

            # Search for movie in TMDB
            movie_data = tmdb_client.search_movie(title, year)

            if not movie_data:
                print(f"   ❌ Skipping '{title}' ({year}) - not found in TMDB")
                skipped += 1
                continue

            # Check if movie exists in database
            existing_movie = get_movie_by_tmdb_id(movie_data['tmdb_id'])

            if not existing_movie:
                # Add movie to database
                movie_id = add_movie(
                    tmdb_id=movie_data['tmdb_id'],
                    title=movie_data['title'],
                    year=movie_data['year'],
                    genres=movie_data['genres'],
                    poster_path=movie_data['poster_path'],
                    streaming_providers=movie_data['streaming_providers'],
                    overview=movie_data['overview']
                )
            else:
                movie_id = existing_movie['id']

            # Add rating for friend
            add_rating(movie_id, rating, watched_date, user=friend_name)
            imported += 1

            if imported % 10 == 0:
                print(f"   ✓ Imported {imported} ratings...")

    print(f"\n✅ Import complete!")
    print(f"   Imported: {imported}")
    print(f"   Skipped: {skipped}")

    return imported


def calculate_compatibility(user: str = 'vikram14s', friend_name: str = None):
    """Calculate taste compatibility between user and friend using Pearson correlation."""
    print(f"\n🤝 Calculating compatibility between {user} and {friend_name}...")

    # Get all ratings for both users
    user_ratings = get_all_ratings(user)
    friend_ratings = get_all_ratings(friend_name)

    # Create rating dictionaries keyed by movie_id
    user_dict = {r['movie_id']: r['rating'] for r in user_ratings}
    friend_dict = {r['movie_id']: r['rating'] for r in friend_ratings}

    # Find common movies
    common_movies = set(user_dict.keys()) & set(friend_dict.keys())

    if len(common_movies) < 5:
        print(f"   ⚠️  Only {len(common_movies)} movies in common - need at least 5 for reliable correlation")
        compatibility = 0.0
    else:
        # Calculate Pearson correlation
        user_ratings_array = [user_dict[m] for m in common_movies]
        friend_ratings_array = [friend_dict[m] for m in common_movies]

        correlation, p_value = pearsonr(user_ratings_array, friend_ratings_array)
        # Convert to 0-100 scale (correlation is -1 to 1)
        compatibility = (correlation + 1) * 50

        print(f"   Common movies: {len(common_movies)}")
        print(f"   Pearson correlation: {correlation:.3f}")
        print(f"   Compatibility: {compatibility:.1f}%")

    # Update friend's compatibility score
    update_friend_compatibility(friend_name, compatibility)

    return compatibility


def main():
    if len(sys.argv) < 3:
        print("Usage: python backend/friends_import.py <friend_name> <path_to_ratings.csv>")
        print("\nExample:")
        print("  python backend/friends_import.py \"Priya\" data/letterboxd/priya_ratings.csv")
        sys.exit(1)

    friend_name = sys.argv[1]
    csv_path = sys.argv[2]

    print("=" * 60)
    print("🎬 LETTERBOXD FRIEND IMPORT")
    print("=" * 60)

    # Add friend to database
    friend_id = add_friend(friend_name)
    print(f"✅ Added friend: {friend_name} (ID: {friend_id})")

    # Import ratings
    imported_count = import_friend_ratings(friend_name, csv_path)

    if imported_count > 0:
        # Calculate compatibility
        compatibility = calculate_compatibility(friend_name=friend_name)

        print("\n" + "=" * 60)
        print("✅ IMPORT COMPLETE!")
        print("=" * 60)
        print(f"Friend: {friend_name}")
        print(f"Ratings imported: {imported_count}")
        print(f"Compatibility: {compatibility:.1f}%")
        print("\nNext step: Enable friend recommendations in settings")
    else:
        print("\n⚠️  No ratings imported. Check the CSV file path.")


if __name__ == '__main__':
    main()
