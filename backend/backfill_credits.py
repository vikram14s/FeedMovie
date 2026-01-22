"""
Backfill director and cast data for existing movies in the database.
"""

import sqlite3
import json
import os
from tmdb_client import get_movie_credits, get_movie_details

# Use the same database path as the app
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'feedmovie.db')


def backfill_credits():
    """Update all movies with director and cast information."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all movies that don't have director/cast data
    cursor.execute('''
        SELECT id, tmdb_id, title, directors, cast_members
        FROM movies
        WHERE tmdb_id IS NOT NULL
    ''')

    movies = cursor.fetchall()
    print(f"Found {len(movies)} movies to check")

    updated = 0
    for movie in movies:
        # Skip if already has data
        if movie['directors'] and movie['cast_members']:
            continue

        tmdb_id = movie['tmdb_id']
        print(f"Fetching credits for: {movie['title']} (TMDB: {tmdb_id})")

        try:
            # Get credits from TMDB
            credits = get_movie_credits(tmdb_id)
            directors = credits.get('directors', [])
            cast = credits.get('cast', [])

            if directors or cast:
                cursor.execute('''
                    UPDATE movies
                    SET directors = ?, cast_members = ?
                    WHERE id = ?
                ''', (
                    json.dumps(directors) if directors else None,
                    json.dumps(cast) if cast else None,
                    movie['id']
                ))
                updated += 1
                print(f"  -> Directors: {directors}")
                print(f"  -> Cast: {cast[:3]}")

        except Exception as e:
            print(f"  -> Error: {e}")

    conn.commit()
    conn.close()

    print(f"\nDone! Updated {updated} movies with credits data.")


if __name__ == '__main__':
    backfill_credits()
