"""
Import Letterboxd ratings from CSV export.

Usage:
    python letterboxd_import.py data/letterboxd/ratings.csv
"""

import csv
import sys
from typing import Dict, Any
from database import init_database, add_movie, add_rating, get_movie_by_tmdb_id
from tmdb_client import search_movie


def parse_letterboxd_rating(rating_str: str) -> float:
    """Convert Letterboxd rating (e.g., '4.5') to float."""
    if not rating_str:
        return 0.0
    try:
        return float(rating_str)
    except ValueError:
        return 0.0


def import_letterboxd_csv(csv_path: str, user: str = 'vikram14s'):
    """
    Import ratings from Letterboxd CSV export.

    Expected CSV columns:
    - Name (movie title)
    - Year
    - Rating (0.5 to 5.0, in 0.5 increments)
    - WatchedDate (optional)
    """
    print(f"Importing Letterboxd data from {csv_path}...")

    init_database()  # Ensure database exists

    imported_count = 0
    skipped_count = 0
    total_count = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_count += 1

            # Extract fields (handle different CSV formats)
            title = row.get('Name') or row.get('Title') or row.get('title')
            year_str = row.get('Year') or row.get('year') or ''
            rating_str = row.get('Rating') or row.get('rating') or ''
            watched_date = row.get('WatchedDate') or row.get('Watched Date') or row.get('watched_date') or None

            if not title:
                print(f"  Skipping row {total_count}: No title found")
                skipped_count += 1
                continue

            # Parse year
            try:
                year = int(year_str) if year_str else None
            except ValueError:
                year = None

            # Parse rating
            rating = parse_letterboxd_rating(rating_str)
            if rating == 0.0:
                print(f"  Skipping '{title}' ({year}): No rating")
                skipped_count += 1
                continue

            # Search for movie in TMDB
            print(f"  [{total_count}/{total_count}] Searching for '{title}' ({year})...")
            movie_data = search_movie(title, year)

            if not movie_data:
                print(f"    ⚠️  Not found in TMDB, skipping")
                skipped_count += 1
                continue

            # Check if already in database
            existing = get_movie_by_tmdb_id(movie_data['tmdb_id'])
            if existing:
                movie_id = existing['id']
                print(f"    ✓ Already in DB (ID: {movie_id})")
            else:
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
                print(f"    ✓ Added to DB (ID: {movie_id})")

            # Add rating
            add_rating(movie_id, rating, watched_date, user)
            imported_count += 1

    print(f"\n✅ Import complete!")
    print(f"   Total rows: {total_count}")
    print(f"   Imported: {imported_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Success rate: {imported_count/total_count*100:.1f}%")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python letterboxd_import.py <path_to_ratings.csv>")
        print("\nExample:")
        print("  python letterboxd_import.py data/letterboxd/ratings.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    import_letterboxd_csv(csv_path)
