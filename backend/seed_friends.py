"""
Seed dummy friend profiles with activity for testing the feed.
Creates archetype users with different movie tastes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_connection, add_movie, create_activity,
    create_user, get_user_by_username, add_friend
)
from auth import hash_password
import tmdb_client

# Archetype friends with their favorite movies
FRIEND_ARCHETYPES = [
    {
        'username': 'action_andy',
        'email': 'andy@example.com',
        'bio': 'Explosions and car chases are my jam',
        'movies': [
            ('Mad Max: Fury Road', 2015, 5.0, 'Absolute masterpiece of action cinema'),
            ('John Wick', 2014, 4.5, 'Keanu delivers'),
            ('Top Gun: Maverick', 2022, 4.5, 'Best sequel ever made'),
            ('The Raid', 2011, 5.0, None),
        ]
    },
    {
        'username': 'indie_iris',
        'email': 'iris@example.com',
        'bio': 'A24 stan, Letterboxd power user',
        'movies': [
            ('Everything Everywhere All at Once', 2022, 5.0, 'Changed my life'),
            ('Moonlight', 2016, 5.0, 'Poetry on screen'),
            ('Lady Bird', 2017, 4.5, 'Greta knows coming-of-age'),
            ('The Lobster', 2015, 4.0, 'Weird but brilliant'),
        ]
    },
    {
        'username': 'scifi_sam',
        'email': 'sam@example.com',
        'bio': 'If it has spaceships, I watched it',
        'movies': [
            ('Dune', 2021, 5.0, 'Villeneuve is a god'),
            ('Arrival', 2016, 5.0, 'Made me cry about linguistics'),
            ('Blade Runner 2049', 2017, 5.0, 'Visual masterpiece'),
            ('Interstellar', 2014, 4.5, None),
        ]
    },
    {
        'username': 'horror_hannah',
        'email': 'hannah@example.com',
        'bio': 'Sleep is overrated anyway',
        'movies': [
            ('Hereditary', 2018, 5.0, 'Toni Collette was robbed'),
            ('The Witch', 2015, 4.5, 'Wouldst thou like to live deliciously?'),
            ('Get Out', 2017, 5.0, 'Social horror done right'),
            ('Midsommar', 2019, 4.0, 'Breakup movie of the decade'),
        ]
    },
    {
        'username': 'comedy_chris',
        'email': 'chris@example.com',
        'bio': 'Life is too short for sad movies',
        'movies': [
            ('The Grand Budapest Hotel', 2014, 5.0, 'Wes Anderson peak'),
            ('Superbad', 2007, 4.5, 'Still quotable after all these years'),
            ('Barbie', 2023, 4.5, 'Kenough said'),
            ('The Big Lebowski', 1998, 5.0, 'The dude abides'),
        ]
    },
]


def create_friend_user(archetype):
    """Create a user account for a friend archetype."""
    username = archetype['username']

    # Check if user already exists
    existing = get_user_by_username(username)
    if existing:
        print(f"  User {username} already exists (id: {existing['id']})")
        return existing['id']

    # Create new user
    password_hash = hash_password('friend123')
    user_id = create_user(archetype['email'], password_hash, username)

    if user_id:
        # Update bio
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET bio = ? WHERE id = ?', (archetype['bio'], user_id))
        conn.commit()
        conn.close()
        print(f"  Created user {username} (id: {user_id})")

    return user_id


def add_movie_activity(user_id, title, year, rating, review_text):
    """Add a movie and create activity for it."""
    # Search for movie on TMDB
    movie_data = tmdb_client.search_movie(title, year)
    if not movie_data:
        print(f"    Could not find: {title} ({year})")
        return

    # Add to database
    movie_id = add_movie(
        tmdb_id=movie_data['tmdb_id'],
        title=movie_data['title'],
        year=movie_data['year'],
        genres=movie_data.get('genres', []),
        poster_path=movie_data.get('poster_path'),
        streaming_providers=movie_data.get('streaming_providers', {}),
        overview=movie_data.get('overview', ''),
        tmdb_rating=movie_data.get('tmdb_rating')
    )

    # Create activity
    action_type = 'reviewed' if review_text else 'rated'
    create_activity(user_id, action_type, movie_id, rating, review_text)
    print(f"    Added: {title} - {rating}★" + (f' "{review_text[:30]}..."' if review_text else ''))


def add_as_friend_for_user(friend_user_id, target_user_id, friend_username):
    """Add friend relationship so activity shows in feed."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get the friend's username to use as the friend name
    cursor.execute('SELECT username FROM users WHERE id = ?', (friend_user_id,))
    friend = cursor.fetchone()

    if friend:
        # Add to friends table for the target user
        cursor.execute('''
            INSERT OR REPLACE INTO friends (user_id, name, letterboxd_username)
            VALUES (?, ?, ?)
        ''', (target_user_id, friend['username'], friend['username']))
        conn.commit()

    conn.close()


def seed_friends(target_username='test'):
    """Seed all friend archetypes and their activity."""
    print(f"\nSeeding friend profiles for user: {target_username}")
    print("=" * 50)

    # Get target user
    target_user = get_user_by_username(target_username)
    if not target_user:
        print(f"Target user '{target_username}' not found!")
        return

    target_user_id = target_user['id']
    print(f"Target user ID: {target_user_id}\n")

    for archetype in FRIEND_ARCHETYPES:
        print(f"\nCreating {archetype['username']}...")

        # Create user account
        friend_user_id = create_friend_user(archetype)
        if not friend_user_id:
            continue

        # Add as friend for target user
        add_as_friend_for_user(friend_user_id, target_user_id, archetype['username'])
        print(f"  Added as friend for {target_username}")

        # Add movie activities
        print(f"  Adding movie activity...")
        for title, year, rating, review in archetype['movies']:
            add_movie_activity(friend_user_id, title, year, rating, review)

    print("\n" + "=" * 50)
    print("Done! Friend activity has been seeded.")
    print("Refresh the Feed tab to see friend activity.")


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'test'
    seed_friends(target)
