"""
Database setup and helpers for FeedMovie.
Simple SQLite with 3 tables: movies, ratings, recommendations.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE_PATH = 'data/feedmovie.db'


def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_database():
    """Initialize the database with schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Movies table: TMDB-enriched with streaming data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            year INTEGER,
            genres TEXT,  -- JSON array
            poster_path TEXT,
            streaming_providers TEXT,  -- JSON: {Netflix, Prime, etc.}
            overview TEXT,
            imdb_id TEXT,
            tmdb_rating REAL,
            imdb_rating REAL,
            rt_rating TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ratings table: Letterboxd data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            rating REAL NOT NULL,  -- 0.5 to 5.0
            watched_date DATE,
            user TEXT DEFAULT 'vikram14s',  -- Add friends later
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')

    # Recommendations table: AI + CF results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            source TEXT NOT NULL,  -- 'claude', 'chatgpt', 'gemini', 'cf', 'friend:<name>'
            score REAL NOT NULL,
            reasoning TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shown_to_user BOOLEAN DEFAULT FALSE,
            swipe_action TEXT,  -- 'left', 'right', null
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')

    # Friends table: Letterboxd friends for taste matching
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            letterboxd_username TEXT,
            compatibility_score REAL,  -- Calculated correlation with user
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Settings table: User preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Set default settings
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value)
        VALUES ('friend_recommendations_enabled', 'false')
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DATABASE_PATH}")


def add_movie(tmdb_id: int, title: str, year: int,
              genres: List[str], poster_path: Optional[str],
              streaming_providers: Dict[str, Any], overview: str,
              imdb_id: Optional[str] = None, tmdb_rating: Optional[float] = None,
              imdb_rating: Optional[float] = None, rt_rating: Optional[str] = None) -> int:
    """Add a movie to the database or return existing ID."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if movie already exists
    cursor.execute('SELECT id FROM movies WHERE tmdb_id = ?', (tmdb_id,))
    existing = cursor.fetchone()
    if existing:
        # Update existing movie with new data (especially ratings)
        # Only update if we have new values
        updates = []
        params = []

        if imdb_id:
            updates.append("imdb_id = ?")
            params.append(imdb_id)
        if tmdb_rating is not None:
            updates.append("tmdb_rating = ?")
            params.append(tmdb_rating)
        if imdb_rating is not None:
            updates.append("imdb_rating = ?")
            params.append(imdb_rating)
        if rt_rating:
            updates.append("rt_rating = ?")
            params.append(rt_rating)
        if poster_path:
            updates.append("poster_path = ?")
            params.append(poster_path)
        if streaming_providers:
            updates.append("streaming_providers = ?")
            params.append(json.dumps(streaming_providers))

        if updates:
            params.append(tmdb_id)
            cursor.execute(f'''
                UPDATE movies
                SET {", ".join(updates)}
                WHERE tmdb_id = ?
            ''', params)
            conn.commit()

        conn.close()
        return existing['id']

    # Insert new movie
    cursor.execute('''
        INSERT INTO movies (tmdb_id, title, year, genres, poster_path,
                          streaming_providers, overview, imdb_id, tmdb_rating,
                          imdb_rating, rt_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tmdb_id, title, year, json.dumps(genres), poster_path,
          json.dumps(streaming_providers), overview, imdb_id, tmdb_rating,
          imdb_rating, rt_rating))

    movie_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return movie_id


def add_rating(movie_id: int, rating: float, watched_date: Optional[str] = None,
               user: str = 'vikram14s'):
    """Add a rating to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO ratings (movie_id, rating, watched_date, user)
        VALUES (?, ?, ?, ?)
    ''', (movie_id, rating, watched_date, user))

    conn.commit()
    conn.close()


def add_recommendation(movie_id: int, source: str, score: float,
                      reasoning: Optional[str] = None):
    """Add a recommendation to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO recommendations (movie_id, source, score, reasoning)
        VALUES (?, ?, ?, ?)
    ''', (movie_id, source, score, reasoning))

    conn.commit()
    conn.close()


def get_all_ratings(user: str = 'vikram14s') -> List[Dict[str, Any]]:
    """Get all ratings for a user with movie details."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.rating, r.watched_date, m.title, m.year, m.tmdb_id, m.genres
        FROM ratings r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.user = ?
        ORDER BY r.rating DESC
    ''', (user,))

    ratings = []
    for row in cursor.fetchall():
        ratings.append({
            'rating': row['rating'],
            'watched_date': row['watched_date'],
            'title': row['title'],
            'year': row['year'],
            'tmdb_id': row['tmdb_id'],
            'genres': json.loads(row['genres']) if row['genres'] else []
        })

    conn.close()
    return ratings


def get_movie_by_tmdb_id(tmdb_id: int) -> Optional[Dict[str, Any]]:
    """Get a movie by TMDB ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM movies WHERE tmdb_id = ?', (tmdb_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'id': row['id'],
        'tmdb_id': row['tmdb_id'],
        'title': row['title'],
        'year': row['year'],
        'genres': json.loads(row['genres']) if row['genres'] else [],
        'poster_path': row['poster_path'],
        'streaming_providers': json.loads(row['streaming_providers']) if row['streaming_providers'] else {},
        'overview': row['overview']
    }


def get_watched_movie_ids() -> List[int]:
    """Get list of TMDB IDs for movies the user has watched."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT m.tmdb_id
        FROM ratings r
        JOIN movies m ON r.movie_id = m.id
    ''')

    movie_ids = [row['tmdb_id'] for row in cursor.fetchall()]
    conn.close()
    return movie_ids


def clear_recommendations():
    """Clear all existing recommendations (for regeneration)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recommendations')
    conn.commit()
    conn.close()
    print("Cleared existing recommendations")


def get_top_recommendations(limit: int = 50, genres: Optional[List[str]] = None) -> tuple[List[Dict[str, Any]], int]:
    """Get top recommendations with movie details, optionally filtered by genres.
    Returns: (list of recommendations, total count of unshown)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all results (use MAX for reasoning to get just one, not concatenated)
    cursor.execute('''
        SELECT
            m.title, m.year, m.poster_path, m.genres, m.overview,
            m.streaming_providers, m.tmdb_id, m.imdb_id,
            m.tmdb_rating, m.imdb_rating, m.rt_rating,
            GROUP_CONCAT(DISTINCT r.source) as sources,
            AVG(r.score) as avg_score,
            MAX(r.reasoning) as reasoning,
            rt.rating as user_rating
        FROM recommendations r
        JOIN movies m ON r.movie_id = m.id
        LEFT JOIN ratings rt ON m.id = rt.movie_id AND rt.user = 'vikram14s'
        WHERE r.shown_to_user = FALSE
        GROUP BY m.id
        ORDER BY avg_score DESC, COUNT(r.id) DESC
    ''')

    all_recommendations = []
    filtered_recommendations = []

    for row in cursor.fetchall():
        movie_genres = json.loads(row['genres']) if row['genres'] else []

        rec = {
            'title': row['title'],
            'year': row['year'],
            'poster_path': row['poster_path'],
            'genres': movie_genres,
            'overview': row['overview'],
            'streaming_providers': json.loads(row['streaming_providers']) if row['streaming_providers'] else {},
            'tmdb_id': row['tmdb_id'],
            'imdb_id': row['imdb_id'],
            'tmdb_rating': row['tmdb_rating'],
            'imdb_rating': row['imdb_rating'],
            'rt_rating': row['rt_rating'],
            'sources': row['sources'].split(',') if row['sources'] else [],
            'score': row['avg_score'],
            'reasoning': row['reasoning'],
            'already_watched': row['user_rating'] is not None,
            'user_rating': row['user_rating']
        }

        all_recommendations.append(rec)

        # Check if it matches the genre filter
        if genres:
            genre_match = any(
                selected_genre.lower() in [g.lower() for g in movie_genres]
                for selected_genre in genres
            )
            if genre_match:
                filtered_recommendations.append(rec)

    conn.close()

    # Return filtered results if genre filter is active, otherwise all
    if genres:
        # Ensure at least 5 movies per genre if possible
        genre_buckets = {genre: [] for genre in genres}

        # Distribute movies into genre buckets
        for rec in filtered_recommendations:
            for genre in genres:
                if genre.lower() in [g.lower() for g in rec['genres']]:
                    genre_buckets[genre].append(rec)

        # Try to get at least 5 from each genre
        result = []
        seen_tmdb_ids = set()

        # First pass: get 5 from each genre
        for genre in genres:
            count = 0
            for rec in genre_buckets[genre]:
                if rec['tmdb_id'] not in seen_tmdb_ids and count < 5:
                    result.append(rec)
                    seen_tmdb_ids.add(rec['tmdb_id'])
                    count += 1

        # Second pass: fill remaining slots with any matching movies
        for rec in filtered_recommendations:
            if rec['tmdb_id'] not in seen_tmdb_ids and len(result) < limit:
                result.append(rec)
                seen_tmdb_ids.add(rec['tmdb_id'])

        total_count = len(filtered_recommendations)
        return result, total_count
    else:
        total_count = len(all_recommendations)
        return all_recommendations[:limit], total_count


def record_swipe(tmdb_id: int, action: str):
    """Record a swipe action (left/right) for a movie."""
    conn = get_connection()
    cursor = conn.cursor()

    # Update all recommendations for this movie
    cursor.execute('''
        UPDATE recommendations
        SET swipe_action = ?, shown_to_user = TRUE
        WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)
    ''', (action, tmdb_id))

    conn.commit()
    conn.close()


def get_watchlist(user: str = 'vikram14s') -> List[Dict[str, Any]]:
    """Get all movies the user has liked (swiped right on)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT
            m.title, m.year, m.poster_path, m.genres, m.overview,
            m.streaming_providers, m.tmdb_id,
            GROUP_CONCAT(r.source) as sources,
            AVG(r.score) as avg_score,
            GROUP_CONCAT(r.reasoning, ' | ') as all_reasoning,
            rt.rating as user_rating,
            MAX(r.id) as latest_rec_id
        FROM recommendations r
        JOIN movies m ON r.movie_id = m.id
        LEFT JOIN ratings rt ON m.id = rt.movie_id AND rt.user = ?
        WHERE r.swipe_action = 'right'
        GROUP BY m.id
        ORDER BY latest_rec_id DESC
    ''', (user,))

    watchlist = []
    for row in cursor.fetchall():
        watchlist.append({
            'title': row['title'],
            'year': row['year'],
            'poster_path': row['poster_path'],
            'genres': json.loads(row['genres']) if row['genres'] else [],
            'overview': row['overview'],
            'streaming_providers': json.loads(row['streaming_providers']) if row['streaming_providers'] else {},
            'tmdb_id': row['tmdb_id'],
            'sources': row['sources'].split(',') if row['sources'] else [],
            'score': row['avg_score'],
            'reasoning': row['all_reasoning'],
            'already_watched': row['user_rating'] is not None,
            'user_rating': row['user_rating']
        })

    conn.close()
    return watchlist


def remove_from_watchlist(tmdb_id: int):
    """Remove a movie from the watchlist (set swipe_action to NULL)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE recommendations
        SET swipe_action = NULL
        WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)
    ''', (tmdb_id,))

    conn.commit()
    conn.close()


def add_friend(name: str, letterboxd_username: str = None) -> int:
    """Add a new friend."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO friends (name, letterboxd_username)
        VALUES (?, ?)
    ''', (name, letterboxd_username))

    friend_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return friend_id


def get_all_friends() -> List[Dict[str, Any]]:
    """Get all friends."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM friends ORDER BY compatibility_score DESC NULLS LAST')
    friends = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return friends


def update_friend_compatibility(name: str, score: float):
    """Update a friend's compatibility score."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE friends
        SET compatibility_score = ?
        WHERE name = ?
    ''', (score, name))

    conn.commit()
    conn.close()


def get_setting(key: str, default: str = None) -> str:
    """Get a setting value."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()

    conn.close()
    return row['value'] if row else default


def set_setting(key: str, value: str):
    """Set a setting value."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (key, value))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    # Initialize database when run directly
    init_database()
    print("Database setup complete!")
