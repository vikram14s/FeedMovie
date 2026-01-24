"""
Database setup and helpers for FeedMovie.
Multi-user platform with movies, ratings, recommendations, and user management.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

import os
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'feedmovie.db')


# ============================================================
# USER MANAGEMENT
# ============================================================

def create_user(email: str, password_hash: str, username: str) -> Optional[int]:
    """Create a new user. Returns user_id or None if email/username exists."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (email, password_hash, username)
            VALUES (?, ?, ?)
        ''', (email, password_hash, username))
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def update_user_onboarding(user_id: int, onboarding_type: str = None,
                           letterboxd_username: str = None,
                           genre_preferences: List[str] = None,
                           onboarding_completed: bool = None):
    """Update user's onboarding status and preferences."""
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if onboarding_type is not None:
        updates.append("onboarding_type = ?")
        params.append(onboarding_type)

    if letterboxd_username is not None:
        updates.append("letterboxd_username = ?")
        params.append(letterboxd_username)

    if genre_preferences is not None:
        updates.append("genre_preferences = ?")
        params.append(json.dumps(genre_preferences))

    if onboarding_completed is not None:
        updates.append("onboarding_completed = ?")
        params.append(onboarding_completed)

    if updates:
        params.append(user_id)
        cursor.execute(f'''
            UPDATE users SET {", ".join(updates)} WHERE id = ?
        ''', params)
        conn.commit()

    conn.close()


def get_connection():
    """Get a connection to the SQLite database."""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_database():
    """Initialize the database with schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table: Multi-user support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            letterboxd_username TEXT,
            onboarding_type TEXT,
            onboarding_completed BOOLEAN DEFAULT FALSE,
            genre_preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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
            directors TEXT,  -- JSON array
            cast_members TEXT,  -- JSON array
            awards TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ratings table: User ratings with user_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            rating REAL NOT NULL,  -- 0.5 to 5.0
            watched_date DATE,
            user TEXT DEFAULT 'vikram14s',  -- Legacy field for backward compat
            user_id INTEGER,  -- New: proper FK to users
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Recommendations table: AI + CF results with user_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            user_id INTEGER,  -- New: per-user recommendations
            source TEXT NOT NULL,  -- 'claude', 'chatgpt', 'gemini', 'cf', 'friend:<name>'
            score REAL NOT NULL,
            reasoning TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shown_to_user BOOLEAN DEFAULT FALSE,
            swipe_action TEXT,  -- 'left', 'right', null
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Friends table: Letterboxd friends for taste matching with user_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,  -- New: per-user friends
            name TEXT NOT NULL,
            letterboxd_username TEXT,
            compatibility_score REAL,  -- Calculated correlation with user
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, name)
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

    # User taste profiles table with user_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_taste_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,  -- New: per-user profiles
            profile_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Onboarding movies table: Popular movies for swipe onboarding
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS onboarding_movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            year INTEGER,
            poster_path TEXT,
            genres TEXT,
            popularity_rank INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Reviews table: User reviews with optional text
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            rating REAL NOT NULL,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            UNIQUE(user_id, movie_id)
        )
    ''')

    # Activity feed table: Track all user actions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            rating REAL,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')

    # Activity likes table: Users liking friend activity
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (activity_id) REFERENCES activity(id),
            UNIQUE(user_id, activity_id)
        )
    ''')

    # Generation jobs table: Track recommendation generation progress
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generation_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            stage TEXT,
            progress INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            duration_seconds REAL,
            error_message TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Set default settings
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value)
        VALUES ('friend_recommendations_enabled', 'false')
    ''')

    conn.commit()
    conn.close()

    # Run migrations for existing databases
    run_migrations()

    print(f"Database initialized at {DATABASE_PATH}")


def run_migrations():
    """Run database migrations to add user_id columns to existing tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if user_id column exists in ratings table
    cursor.execute("PRAGMA table_info(ratings)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'user_id' not in columns:
        print("Running migration: Adding user_id to ratings table...")
        try:
            cursor.execute('ALTER TABLE ratings ADD COLUMN user_id INTEGER REFERENCES users(id)')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column might already exist

    # Check recommendations table
    cursor.execute("PRAGMA table_info(recommendations)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'user_id' not in columns:
        print("Running migration: Adding user_id to recommendations table...")
        try:
            cursor.execute('ALTER TABLE recommendations ADD COLUMN user_id INTEGER REFERENCES users(id)')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Check friends table
    cursor.execute("PRAGMA table_info(friends)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'user_id' not in columns:
        print("Running migration: Adding user_id to friends table...")
        try:
            cursor.execute('ALTER TABLE friends ADD COLUMN user_id INTEGER REFERENCES users(id)')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Check user_taste_profiles table
    cursor.execute("PRAGMA table_info(user_taste_profiles)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'user_id' not in columns:
        print("Running migration: Adding user_id to user_taste_profiles table...")
        try:
            cursor.execute('ALTER TABLE user_taste_profiles ADD COLUMN user_id INTEGER REFERENCES users(id)')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Check users table for bio and profile_picture_url columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'bio' not in columns:
        print("Running migration: Adding bio to users table...")
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN bio TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    if 'profile_picture_url' not in columns:
        print("Running migration: Adding profile_picture_url to users table...")
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN profile_picture_url TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    conn.close()


def add_movie(tmdb_id: int, title: str, year: int,
              genres: List[str], poster_path: Optional[str],
              streaming_providers: Dict[str, Any], overview: str,
              imdb_id: Optional[str] = None, tmdb_rating: Optional[float] = None,
              imdb_rating: Optional[float] = None, rt_rating: Optional[str] = None,
              directors: Optional[List[str]] = None, cast: Optional[List[str]] = None,
              awards: Optional[str] = None) -> int:
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
        if directors:
            updates.append("directors = ?")
            params.append(json.dumps(directors))
        if cast:
            updates.append("cast_members = ?")
            params.append(json.dumps(cast))
        if awards:
            updates.append("awards = ?")
            params.append(awards)

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
                          imdb_rating, rt_rating, directors, cast_members, awards)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tmdb_id, title, year, json.dumps(genres), poster_path,
          json.dumps(streaming_providers), overview, imdb_id, tmdb_rating,
          imdb_rating, rt_rating, json.dumps(directors) if directors else None,
          json.dumps(cast) if cast else None, awards))

    movie_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return movie_id


def add_rating(movie_id: int, rating: float, watched_date: Optional[str] = None,
               user: str = 'vikram14s', user_id: Optional[int] = None):
    """Add a rating to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO ratings (movie_id, rating, watched_date, user, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (movie_id, rating, watched_date, user, user_id))

    conn.commit()
    conn.close()


def add_recommendation(movie_id: int, source: str, score: float,
                      reasoning: Optional[str] = None, user_id: Optional[int] = None):
    """Add a recommendation to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO recommendations (movie_id, source, score, reasoning, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (movie_id, source, score, reasoning, user_id))

    conn.commit()
    conn.close()


def get_all_ratings(user: str = 'vikram14s', user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all ratings for a user with movie details."""
    conn = get_connection()
    cursor = conn.cursor()

    # Use user_id if provided, otherwise fall back to legacy user string
    if user_id is not None:
        cursor.execute('''
            SELECT r.rating, r.watched_date, m.title, m.year, m.tmdb_id, m.genres
            FROM ratings r
            JOIN movies m ON r.movie_id = m.id
            WHERE r.user_id = ?
            ORDER BY r.rating DESC
        ''', (user_id,))
    else:
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


def get_watched_movie_ids(user: str = 'vikram14s', user_id: Optional[int] = None) -> List[int]:
    """Get list of TMDB IDs for movies the user has watched."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('''
            SELECT DISTINCT m.tmdb_id
            FROM ratings r
            JOIN movies m ON r.movie_id = m.id
            WHERE r.user_id = ?
        ''', (user_id,))
    else:
        cursor.execute('''
            SELECT DISTINCT m.tmdb_id
            FROM ratings r
            JOIN movies m ON r.movie_id = m.id
            WHERE r.user = ?
        ''', (user,))

    movie_ids = [row['tmdb_id'] for row in cursor.fetchall()]
    conn.close()
    return movie_ids


def clear_recommendations(user_id: Optional[int] = None):
    """Clear existing recommendations (for regeneration). If user_id provided, only clears that user's."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('DELETE FROM recommendations WHERE user_id = ?', (user_id,))
    else:
        cursor.execute('DELETE FROM recommendations')

    conn.commit()
    conn.close()
    print(f"Cleared recommendations" + (f" for user {user_id}" if user_id else ""))


def get_top_recommendations(limit: int = 50, genres: Optional[List[str]] = None,
                           user_id: Optional[int] = None) -> tuple[List[Dict[str, Any]], int]:
    """Get top recommendations with movie details, optionally filtered by genres.
    Returns: (list of recommendations, total count of unshown)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build query with optional user_id filter
    if user_id is not None:
        cursor.execute('''
            SELECT
                m.title, m.year, m.poster_path, m.genres, m.overview,
                m.streaming_providers, m.tmdb_id, m.imdb_id,
                m.tmdb_rating, m.imdb_rating, m.rt_rating,
                m.directors, m.cast_members, m.awards,
                GROUP_CONCAT(DISTINCT r.source) as sources,
                AVG(r.score) as avg_score,
                MAX(r.reasoning) as reasoning,
                rt.rating as user_rating
            FROM recommendations r
            JOIN movies m ON r.movie_id = m.id
            LEFT JOIN ratings rt ON m.id = rt.movie_id AND rt.user_id = ?
            WHERE r.shown_to_user = FALSE AND r.user_id = ?
            GROUP BY m.id
            ORDER BY avg_score DESC, COUNT(r.id) DESC
        ''', (user_id, user_id))
    else:
        # Legacy query for backward compatibility
        cursor.execute('''
            SELECT
                m.title, m.year, m.poster_path, m.genres, m.overview,
                m.streaming_providers, m.tmdb_id, m.imdb_id,
                m.tmdb_rating, m.imdb_rating, m.rt_rating,
                m.directors, m.cast_members, m.awards,
                GROUP_CONCAT(DISTINCT r.source) as sources,
                AVG(r.score) as avg_score,
                MAX(r.reasoning) as reasoning,
                rt.rating as user_rating
            FROM recommendations r
            JOIN movies m ON r.movie_id = m.id
            LEFT JOIN ratings rt ON m.id = rt.movie_id AND rt.user = 'vikram14s'
            WHERE r.shown_to_user = FALSE AND r.user_id IS NULL
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
            'directors': json.loads(row['directors']) if row['directors'] else [],
            'cast': json.loads(row['cast_members']) if row['cast_members'] else [],
            'awards': row['awards'],
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


def record_swipe(tmdb_id: int, action: str, user_id: Optional[int] = None):
    """Record a swipe action (left/right) for a movie."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('''
            UPDATE recommendations
            SET swipe_action = ?, shown_to_user = TRUE
            WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)
            AND user_id = ?
        ''', (action, tmdb_id, user_id))
    else:
        cursor.execute('''
            UPDATE recommendations
            SET swipe_action = ?, shown_to_user = TRUE
            WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)
            AND user_id IS NULL
        ''', (action, tmdb_id))

    conn.commit()
    conn.close()


def get_watchlist(user: str = 'vikram14s', user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all movies the user has liked (swiped right on)."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('''
            SELECT DISTINCT
                m.title, m.year, m.poster_path, m.genres, m.overview,
                m.streaming_providers, m.tmdb_id,
                m.directors, m.cast_members, m.awards,
                GROUP_CONCAT(r.source) as sources,
                AVG(r.score) as avg_score,
                GROUP_CONCAT(r.reasoning, ' | ') as all_reasoning,
                rt.rating as user_rating,
                MAX(r.id) as latest_rec_id
            FROM recommendations r
            JOIN movies m ON r.movie_id = m.id
            LEFT JOIN ratings rt ON m.id = rt.movie_id AND rt.user_id = ?
            WHERE r.swipe_action = 'right' AND r.user_id = ?
            GROUP BY m.id
            ORDER BY latest_rec_id DESC
        ''', (user_id, user_id))
    else:
        cursor.execute('''
            SELECT DISTINCT
                m.title, m.year, m.poster_path, m.genres, m.overview,
                m.streaming_providers, m.tmdb_id,
                m.directors, m.cast_members, m.awards,
                GROUP_CONCAT(r.source) as sources,
                AVG(r.score) as avg_score,
                GROUP_CONCAT(r.reasoning, ' | ') as all_reasoning,
                rt.rating as user_rating,
                MAX(r.id) as latest_rec_id
            FROM recommendations r
            JOIN movies m ON r.movie_id = m.id
            LEFT JOIN ratings rt ON m.id = rt.movie_id AND rt.user = ?
            WHERE r.swipe_action = 'right' AND r.user_id IS NULL
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
            'directors': json.loads(row['directors']) if row['directors'] else [],
            'cast': json.loads(row['cast_members']) if row['cast_members'] else [],
            'awards': row['awards'],
            'sources': row['sources'].split(',') if row['sources'] else [],
            'score': row['avg_score'],
            'reasoning': row['all_reasoning'],
            'already_watched': row['user_rating'] is not None,
            'user_rating': row['user_rating']
        })

    conn.close()
    return watchlist


def remove_from_watchlist(tmdb_id: int, user_id: Optional[int] = None):
    """Remove a movie from the watchlist (set swipe_action to NULL)."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('''
            UPDATE recommendations
            SET swipe_action = NULL
            WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)
            AND user_id = ?
        ''', (tmdb_id, user_id))
    else:
        cursor.execute('''
            UPDATE recommendations
            SET swipe_action = NULL
            WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)
            AND user_id IS NULL
        ''', (tmdb_id,))

    conn.commit()
    conn.close()


def add_friend(name: str, letterboxd_username: str = None, user_id: Optional[int] = None, curator_username: str = None) -> int:
    """Add a new friend.

    Args:
        name: Display name of the friend
        letterboxd_username: Letterboxd username (for imported friends)
        user_id: The user who is adding this friend
        curator_username: Username of curator account (for system curators)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # If curator_username is provided, use it as the letterboxd_username
    # (the feed query matches on this field to find user accounts)
    effective_username = curator_username or letterboxd_username

    cursor.execute('''
        INSERT OR REPLACE INTO friends (name, letterboxd_username, user_id)
        VALUES (?, ?, ?)
    ''', (name, effective_username, user_id))

    friend_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return friend_id


def get_all_friends(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all friends for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('''
            SELECT * FROM friends
            WHERE user_id = ?
            ORDER BY compatibility_score DESC NULLS LAST
        ''', (user_id,))
    else:
        cursor.execute('''
            SELECT * FROM friends
            WHERE user_id IS NULL
            ORDER BY compatibility_score DESC NULLS LAST
        ''')

    friends = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return friends


def update_friend_compatibility(name: str, score: float, user_id: Optional[int] = None):
    """Update a friend's compatibility score."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('''
            UPDATE friends
            SET compatibility_score = ?
            WHERE name = ? AND user_id = ?
        ''', (score, name, user_id))
    else:
        cursor.execute('''
            UPDATE friends
            SET compatibility_score = ?
            WHERE name = ? AND user_id IS NULL
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


# ============================================================
# ONBOARDING MOVIES
# ============================================================

def add_onboarding_movie(tmdb_id: int, title: str, year: int,
                         poster_path: str, genres: List[str], popularity_rank: int):
    """Add a movie to the onboarding set."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO onboarding_movies
            (tmdb_id, title, year, poster_path, genres, popularity_rank)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tmdb_id, title, year, poster_path, json.dumps(genres), popularity_rank))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_onboarding_movies(limit: int = 20) -> List[Dict[str, Any]]:
    """Get movies for onboarding swipe flow."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tmdb_id, title, year, poster_path, genres
        FROM onboarding_movies
        ORDER BY popularity_rank ASC
        LIMIT ?
    ''', (limit,))

    movies = []
    for row in cursor.fetchall():
        movies.append({
            'tmdb_id': row['tmdb_id'],
            'title': row['title'],
            'year': row['year'],
            'poster_path': row['poster_path'],
            'genres': json.loads(row['genres']) if row['genres'] else []
        })

    conn.close()
    return movies


def get_onboarding_movies_count() -> int:
    """Get count of onboarding movies."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM onboarding_movies')
    count = cursor.fetchone()['count']

    conn.close()
    return count


# ============================================================
# REVIEWS
# ============================================================

def create_or_update_review(user_id: int, movie_id: int, rating: float,
                            review_text: Optional[str] = None) -> int:
    """Create or update a review. Returns review_id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reviews (user_id, movie_id, rating, review_text)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, movie_id) DO UPDATE SET
            rating = excluded.rating,
            review_text = excluded.review_text,
            created_at = CURRENT_TIMESTAMP
    ''', (user_id, movie_id, rating, review_text))

    review_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return review_id


def get_user_reviews(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get reviews by a user with movie details."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id, r.rating, r.review_text, r.created_at,
               m.tmdb_id, m.title, m.year, m.poster_path, m.genres
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
    ''', (user_id, limit))

    reviews = []
    for row in cursor.fetchall():
        reviews.append({
            'id': row['id'],
            'rating': row['rating'],
            'review_text': row['review_text'],
            'created_at': row['created_at'],
            'movie': {
                'tmdb_id': row['tmdb_id'],
                'title': row['title'],
                'year': row['year'],
                'poster_path': row['poster_path'],
                'genres': json.loads(row['genres']) if row['genres'] else []
            }
        })

    conn.close()
    return reviews


def get_movie_reviews(movie_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get reviews for a movie with user details."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id, r.rating, r.review_text, r.created_at,
               u.id as user_id, u.username, u.profile_picture_url
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.movie_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
    ''', (movie_id, limit))

    reviews = []
    for row in cursor.fetchall():
        reviews.append({
            'id': row['id'],
            'rating': row['rating'],
            'review_text': row['review_text'],
            'created_at': row['created_at'],
            'user': {
                'id': row['user_id'],
                'username': row['username'],
                'profile_picture_url': row['profile_picture_url']
            }
        })

    conn.close()
    return reviews


# ============================================================
# ACTIVITY FEED
# ============================================================

def create_activity(user_id: int, action_type: str, movie_id: int,
                   rating: Optional[float] = None, review_text: Optional[str] = None) -> int:
    """Create an activity entry. Returns activity_id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO activity (user_id, action_type, movie_id, rating, review_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, action_type, movie_id, rating, review_text))

    activity_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return activity_id


def get_friends_activity(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get activity feed from user's friends."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get activity from friends (users in the friends table for this user)
    # Matches friends to users via:
    # 1. letterboxd_username to letterboxd_username (for imported Letterboxd friends)
    # 2. letterboxd_username to username (for curators - username stored in letterboxd_username field)
    # 3. name to username (fallback name matching)
    cursor.execute('''
        SELECT a.id, a.action_type, a.rating, a.review_text, a.created_at,
               u.id as user_id, u.username, u.profile_picture_url,
               m.tmdb_id, m.title, m.year, m.poster_path, m.genres,
               m.tmdb_rating, m.overview,
               (SELECT COUNT(*) FROM activity_likes al WHERE al.activity_id = a.id) as like_count,
               (SELECT COUNT(*) FROM activity_likes al WHERE al.activity_id = a.id AND al.user_id = ?) as user_liked
        FROM activity a
        JOIN users u ON a.user_id = u.id
        JOIN movies m ON a.movie_id = m.id
        WHERE a.user_id IN (
            SELECT u2.id FROM friends f
            JOIN users u2 ON f.letterboxd_username = u2.letterboxd_username
            WHERE f.user_id = ? AND f.letterboxd_username IS NOT NULL
        )
        OR a.user_id IN (
            SELECT u2.id FROM friends f
            JOIN users u2 ON LOWER(f.letterboxd_username) = LOWER(u2.username)
            WHERE f.user_id = ? AND f.letterboxd_username IS NOT NULL
        )
        OR a.user_id IN (
            SELECT u2.id FROM friends f
            JOIN users u2 ON LOWER(f.name) = LOWER(u2.username)
            WHERE f.user_id = ?
        )
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
    ''', (user_id, user_id, user_id, user_id, limit, offset))

    activities = []
    for row in cursor.fetchall():
        activities.append({
            'id': row['id'],
            'action_type': row['action_type'],
            'rating': row['rating'],
            'review_text': row['review_text'],
            'created_at': row['created_at'],
            'like_count': row['like_count'],
            'user_liked': row['user_liked'] > 0,
            'user': {
                'id': row['user_id'],
                'username': row['username'],
                'profile_picture_url': row['profile_picture_url']
            },
            'movie': {
                'tmdb_id': row['tmdb_id'],
                'title': row['title'],
                'year': row['year'],
                'poster_path': row['poster_path'],
                'genres': json.loads(row['genres']) if row['genres'] else [],
                'tmdb_rating': row['tmdb_rating'],
                'overview': row['overview']
            }
        })

    conn.close()
    return activities


def get_user_activity(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Get activity for a specific user (for profile page)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT a.id, a.action_type, a.rating, a.review_text, a.created_at,
               m.tmdb_id, m.title, m.year, m.poster_path
        FROM activity a
        JOIN movies m ON a.movie_id = m.id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (user_id, limit))

    activities = []
    for row in cursor.fetchall():
        activities.append({
            'id': row['id'],
            'action_type': row['action_type'],
            'rating': row['rating'],
            'review_text': row['review_text'],
            'created_at': row['created_at'],
            'movie': {
                'tmdb_id': row['tmdb_id'],
                'title': row['title'],
                'year': row['year'],
                'poster_path': row['poster_path']
            }
        })

    conn.close()
    return activities


# ============================================================
# ACTIVITY LIKES
# ============================================================

def like_activity(user_id: int, activity_id: int) -> bool:
    """Like an activity. Returns True if successful."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO activity_likes (user_id, activity_id)
            VALUES (?, ?)
        ''', (user_id, activity_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Already liked
    finally:
        conn.close()


def unlike_activity(user_id: int, activity_id: int) -> bool:
    """Unlike an activity. Returns True if something was deleted."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM activity_likes
        WHERE user_id = ? AND activity_id = ?
    ''', (user_id, activity_id))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ============================================================
# USER PROFILE
# ============================================================

def update_user_profile(user_id: int, bio: Optional[str] = None,
                        profile_picture_url: Optional[str] = None) -> bool:
    """Update user profile fields."""
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if bio is not None:
        updates.append("bio = ?")
        params.append(bio)

    if profile_picture_url is not None:
        updates.append("profile_picture_url = ?")
        params.append(profile_picture_url)

    if not updates:
        conn.close()
        return False

    params.append(user_id)
    cursor.execute(f'''
        UPDATE users SET {", ".join(updates)} WHERE id = ?
    ''', params)

    conn.commit()
    conn.close()
    return True


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get user stats for profile page."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get movie count and average rating from ratings table (includes Letterboxd imports)
    cursor.execute('''
        SELECT COUNT(*) as movie_count, AVG(rating) as avg_rating
        FROM ratings WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    movie_count = row['movie_count'] or 0
    avg_rating = round(row['avg_rating'], 1) if row['avg_rating'] else 0

    # Get favorite genres (most common from rated movies)
    cursor.execute('''
        SELECT m.genres
        FROM ratings r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.user_id = ?
    ''', (user_id,))

    genre_counts = {}
    for row in cursor.fetchall():
        genres = json.loads(row['genres']) if row['genres'] else []
        for genre in genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Get top 3 genres
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    favorite_genres = [g[0] for g in sorted_genres[:3]]

    # Get watchlist count
    cursor.execute('''
        SELECT COUNT(DISTINCT m.id) as watchlist_count
        FROM recommendations r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.swipe_action = 'right' AND r.user_id = ?
    ''', (user_id,))
    watchlist_count = cursor.fetchone()['watchlist_count'] or 0

    conn.close()

    return {
        'movies_watched': movie_count,
        'avg_rating': avg_rating,
        'favorite_genres': favorite_genres,
        'watchlist_count': watchlist_count
    }


def get_user_library(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Get user's rated movies (their library)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.rating, r.watched_date, r.created_at,
               m.tmdb_id, m.title, m.year, m.poster_path, m.genres
        FROM ratings r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
    ''', (user_id, limit))

    library = []
    for row in cursor.fetchall():
        library.append({
            'rating': row['rating'],
            'watched_date': row['watched_date'],
            'created_at': row['created_at'],
            'movie': {
                'tmdb_id': row['tmdb_id'],
                'title': row['title'],
                'year': row['year'],
                'poster_path': row['poster_path'],
                'genres': json.loads(row['genres']) if row['genres'] else []
            }
        })

    conn.close()
    return library


# ============================================================
# GENERATION JOBS (Progress tracking)
# ============================================================

def create_generation_job(user_id: int) -> int:
    """Create a new generation job. Returns job_id."""
    conn = get_connection()
    cursor = conn.cursor()

    # Cancel any existing pending/running jobs for this user
    cursor.execute('''
        UPDATE generation_jobs
        SET status = 'cancelled'
        WHERE user_id = ? AND status IN ('pending', 'running')
    ''', (user_id,))

    cursor.execute('''
        INSERT INTO generation_jobs (user_id, status, stage, progress)
        VALUES (?, 'running', 'starting', 0)
    ''', (user_id,))

    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id


def update_generation_job(job_id: int, stage: str = None, progress: int = None,
                          status: str = None, error_message: str = None):
    """Update a generation job's progress."""
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if stage is not None:
        updates.append("stage = ?")
        params.append(stage)

    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)

    if status is not None:
        updates.append("status = ?")
        params.append(status)
        if status == 'completed':
            updates.append("completed_at = CURRENT_TIMESTAMP")
            updates.append("duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400")

    if error_message is not None:
        updates.append("error_message = ?")
        params.append(error_message)

    if updates:
        params.append(job_id)
        cursor.execute(f'''
            UPDATE generation_jobs SET {", ".join(updates)} WHERE id = ?
        ''', params)
        conn.commit()

    conn.close()


def get_generation_job(user_id: int) -> Optional[Dict[str, Any]]:
    """Get the latest generation job for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM generation_jobs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    ''', (user_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def get_average_generation_time() -> float:
    """Get the average generation time in seconds from completed jobs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT AVG(duration_seconds) as avg_duration
        FROM generation_jobs
        WHERE status = 'completed' AND duration_seconds IS NOT NULL
        AND duration_seconds > 10  -- Ignore very fast jobs (likely cached)
        AND duration_seconds < 600  -- Ignore outliers (> 10 minutes)
    ''')

    row = cursor.fetchone()
    conn.close()

    # Default to 90 seconds if no data
    return row['avg_duration'] if row and row['avg_duration'] else 90.0


if __name__ == '__main__':
    # Initialize database when run directly
    init_database()
    print("Database setup complete!")
