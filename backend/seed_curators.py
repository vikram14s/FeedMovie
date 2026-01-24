"""
Seed curator accounts with pre-populated activity for the feed.
"""

import sqlite3
from database import get_connection, create_user, add_rating, add_movie
from auth import hash_password
from tmdb_client import get_movie_details, search_movies
import random
from datetime import datetime, timedelta

# Curator profiles with their movie preferences
CURATORS = [
    {
        'username': 'The Film Critic',
        'email': 'filmcritic@feedmovie.curator',
        'bio': 'Award-season expert, loves prestige cinema',
        'movies': [
            ('Oppenheimer', 5.0, 'A masterpiece of filmmaking. Nolan at his finest.'),
            ('Past Lives', 4.5, 'Delicate, beautiful, and emotionally devastating.'),
            ('The Holdovers', 4.5, 'Perfectly crafted character study with heart.'),
            ('Killers of the Flower Moon', 5.0, 'Scorsese delivers another epic.'),
            ('Poor Things', 4.5, 'Wildly inventive and brilliantly acted.'),
            ('Anatomy of a Fall', 5.0, 'Gripping courtroom drama. Exceptional.'),
            ('The Zone of Interest', 4.5, 'Haunting and unforgettable.'),
            ('American Fiction', 4.0, 'Sharp satirical edge with great performances.'),
        ]
    },
    {
        'username': 'Popcorn Pete',
        'email': 'popcornpete@feedmovie.curator',
        'bio': 'Blockbuster enthusiast, here for the fun',
        'movies': [
            ('Dune: Part Two', 5.0, 'EPIC! This is what cinema is all about!'),
            ('Top Gun: Maverick', 5.0, 'Pure adrenaline. Saw it 3 times in IMAX!'),
            ('Spider-Man: No Way Home', 5.0, 'Fan service done RIGHT. I cried.'),
            ('Avatar: The Way of Water', 4.5, 'Visually insane. Worth the 3D ticket.'),
            ('John Wick: Chapter 4', 5.0, 'Best action scenes ever filmed.'),
            ('The Batman', 4.5, 'Dark, gritty, and absolutely awesome.'),
            ('Godzilla x Kong', 4.0, 'Giant monsters fighting. What more do you need?'),
            ('Mission: Impossible - Dead Reckoning', 5.0, 'Tom Cruise is superhuman.'),
        ]
    },
    {
        'username': 'Scary Sarah',
        'email': 'scarysarah@feedmovie.curator',
        'bio': 'Horror aficionado, loves a good scare',
        'movies': [
            ('Talk to Me', 5.0, 'Best horror in years. Genuinely terrifying.'),
            ('Smile', 4.0, 'That opening scene had me hooked.'),
            ('Barbarian', 5.0, 'Go in blind. Trust me. WILD ride.'),
            ('Pearl', 4.5, 'Mia Goth is a horror icon now.'),
            ('Hereditary', 5.0, 'Still thinking about that car scene.'),
            ('The Black Phone', 4.0, 'Ethan Hawke is chilling.'),
            ('Nope', 4.5, 'Peele does it again. Loved the alien design.'),
            ('Terrifier 2', 4.0, 'Not for the faint of heart. Art the Clown delivers.'),
        ]
    },
    {
        'username': 'Indie Ian',
        'email': 'indieian@feedmovie.curator',
        'bio': 'Discovers hidden gems before they trend',
        'movies': [
            ('Aftersun', 5.0, 'Destroyed me emotionally. Paul Mescal is incredible.'),
            ('The Worst Person in the World', 5.0, 'Modern romance done perfectly.'),
            ('Drive My Car', 5.0, 'Three hours flew by. Hamaguchi is a master.'),
            ('Petite Maman', 4.5, 'Simple but profound. Beautiful.'),
            ('All of Us Strangers', 5.0, 'Hauntingly gorgeous. Cried for an hour after.'),
            ('Past Lives', 5.0, 'The ending destroyed me in the best way.'),
            ('The Banshees of Inisherin', 4.5, 'Dark comedy perfection.'),
            ('Saint Omer', 4.5, 'Quietly devastating courtroom drama.'),
        ]
    },
    {
        'username': 'Classic Clara',
        'email': 'classicclara@feedmovie.curator',
        'bio': 'Old Hollywood expert, timeless taste',
        'movies': [
            ('Casablanca', 5.0, 'The perfect film. Timeless in every way.'),
            ('12 Angry Men', 5.0, 'A masterclass in tension and dialogue.'),
            ('Sunset Boulevard', 5.0, 'Norma Desmond is unforgettable.'),
            ('Singin\' in the Rain', 5.0, 'Pure joy from start to finish.'),
            ('Vertigo', 5.0, 'Hitchcock\'s haunting masterpiece.'),
            ('The Apartment', 4.5, 'Wilder at his bittersweet best.'),
            ('Some Like It Hot', 5.0, 'Comedy doesn\'t get better than this.'),
            ('Rear Window', 4.5, 'Suspense perfected.'),
        ]
    },
    {
        'username': 'World Cinema Wes',
        'email': 'worldcinemawes@feedmovie.curator',
        'bio': 'Explores films from every corner of the globe',
        'movies': [
            ('Parasite', 5.0, 'Genre-defying brilliance from Korea.'),
            ('City of God', 5.0, 'Brazilian cinema at its most powerful.'),
            ('Amelie', 5.0, 'French whimsy and charm personified.'),
            ('In the Mood for Love', 5.0, 'Wong Kar-wai creates pure poetry.'),
            ('Oldboy', 5.0, 'Korean revenge thriller perfection.'),
            ('Pan\'s Labyrinth', 5.0, 'Del Toro\'s dark fairy tale masterpiece.'),
            ('Cinema Paradiso', 5.0, 'A love letter to movies. Bring tissues.'),
            ('The Lives of Others', 4.5, 'Gripping German drama.'),
        ]
    },
]


def get_or_create_movie(title: str) -> int:
    """Search for a movie and add it to the database if not exists."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if movie exists by title
    cursor.execute('SELECT id, tmdb_id FROM movies WHERE title LIKE ?', (f'%{title}%',))
    row = cursor.fetchone()

    if row:
        conn.close()
        return row['id']

    # Search TMDB for the movie
    try:
        results = search_movies(title)
        if results:
            movie_data = results[0]
            tmdb_id = movie_data['id']

            # Check if this tmdb_id already exists
            cursor.execute('SELECT id FROM movies WHERE tmdb_id = ?', (tmdb_id,))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return existing['id']

            # Get full details
            details = get_movie_details(tmdb_id)
            if details:
                # Insert movie
                cursor.execute('''
                    INSERT INTO movies (tmdb_id, title, year, poster_path, overview, genres, tmdb_rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tmdb_id,
                    details.get('title', title),
                    details.get('release_date', '')[:4] if details.get('release_date') else None,
                    f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}" if details.get('poster_path') else None,
                    details.get('overview', ''),
                    json.dumps([g['name'] for g in details.get('genres', [])]),
                    details.get('vote_average', 0)
                ))
                movie_id = cursor.lastrowid
                conn.commit()
                conn.close()
                return movie_id
    except Exception as e:
        print(f"Error fetching movie '{title}': {e}")

    conn.close()
    return None


def create_curator_account(curator: dict) -> int:
    """Create a curator user account."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if already exists
    cursor.execute('SELECT id FROM users WHERE email = ?', (curator['email'],))
    existing = cursor.fetchone()
    if existing:
        # Update bio
        cursor.execute('UPDATE users SET bio = ? WHERE id = ?', (curator['bio'], existing['id']))
        conn.commit()
        conn.close()
        return existing['id']

    # Create user with a random password (they won't login)
    password_hash = hash_password('curator_no_login_' + curator['username'])

    cursor.execute('''
        INSERT INTO users (email, password_hash, username, bio, onboarding_completed)
        VALUES (?, ?, ?, ?, TRUE)
    ''', (curator['email'], password_hash, curator['username'], curator['bio']))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"Created curator account: {curator['username']} (ID: {user_id})")
    return user_id


def add_curator_activity(user_id: int, movie_id: int, rating: float, review: str, days_ago: int):
    """Add a rating and activity entry for a curator."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if activity already exists for this user/movie
    cursor.execute('SELECT id FROM activity WHERE user_id = ? AND movie_id = ?', (user_id, movie_id))
    if cursor.fetchone():
        conn.close()
        return

    created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

    # Add rating (ratings table doesn't have review_text)
    cursor.execute('''
        INSERT OR IGNORE INTO ratings (user_id, movie_id, rating, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, movie_id, rating, created_at))

    # Add activity (activity table has review_text)
    cursor.execute('''
        INSERT INTO activity (user_id, movie_id, action_type, rating, review_text, created_at)
        VALUES (?, ?, 'rating', ?, ?, ?)
    ''', (user_id, movie_id, rating, review, created_at))

    conn.commit()
    conn.close()


def seed_curators():
    """Main function to seed all curator data."""
    print("Seeding curator accounts and activity...")

    import json  # Import here for the movie insert

    for curator in CURATORS:
        print(f"\nProcessing {curator['username']}...")

        # Create curator account
        user_id = create_curator_account(curator)

        # Add their movie ratings with staggered dates
        for i, (title, rating, review) in enumerate(curator['movies']):
            movie_id = get_or_create_movie(title)
            if movie_id:
                # Stagger activity over the past month
                days_ago = random.randint(1, 30)
                add_curator_activity(user_id, movie_id, rating, review, days_ago)
                print(f"  Added rating for '{title}'")
            else:
                print(f"  Could not find movie: {title}")

    print("\nCurator seeding complete!")


def link_curators_to_user(user_id: int):
    """Add all curators as friends for a specific user."""
    conn = get_connection()
    cursor = conn.cursor()

    for curator in CURATORS:
        # Get curator user id
        cursor.execute('SELECT id FROM users WHERE email = ?', (curator['email'],))
        curator_row = cursor.fetchone()
        if curator_row:
            # Add as friend (by name, matching the friends table structure)
            cursor.execute('''
                INSERT OR IGNORE INTO friends (user_id, name)
                VALUES (?, ?)
            ''', (user_id, curator['username']))

    conn.commit()
    conn.close()
    print(f"Linked all curators as friends for user {user_id}")


if __name__ == '__main__':
    seed_curators()
