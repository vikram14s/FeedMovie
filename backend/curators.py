"""
Curator (Tastemaker) management for FeedMovie.

Creates and maintains system curator accounts with pre-populated activity
so users who follow curators during onboarding see content in their feed.
"""

from database import (
    get_connection, init_database, create_user, get_user_by_username,
    add_movie, get_movie_by_tmdb_id, create_activity
)
import tmdb_client
import bcrypt
import os

# Curator definitions with their recent movies/activity
CURATORS = {
    "The Film Critic": {
        "username": "thefilmcritic",
        "email": "critic@feedmovie.app",
        "bio": "Award-season expert, loves prestige cinema",
        "recent_movies": [
            {"title": "Oppenheimer", "year": 2023, "rating": 5.0, "review": "A masterpiece of epic filmmaking. Nolan at his finest."},
            {"title": "Past Lives", "year": 2023, "rating": 4.5, "review": "Achingly beautiful exploration of fate and connection."},
            {"title": "The Holdovers", "year": 2023, "rating": 4.5, "review": "Paul Giamatti delivers career-best work."},
            {"title": "Killers of the Flower Moon", "year": 2023, "rating": 4.0, "review": "Scorsese's unflinching look at American greed."},
            {"title": "Anatomy of a Fall", "year": 2023, "rating": 4.5, "review": "Riveting courtroom drama with layers of ambiguity."},
        ]
    },
    "Popcorn Pete": {
        "username": "popcornpete",
        "email": "pete@feedmovie.app",
        "bio": "Blockbuster enthusiast, here for the fun",
        "recent_movies": [
            {"title": "Dune: Part Two", "year": 2024, "rating": 5.0, "review": "INCREDIBLE. The sandworm ride scene is everything!"},
            {"title": "Top Gun: Maverick", "year": 2022, "rating": 5.0, "review": "The best action movie in years. Tom Cruise delivers!"},
            {"title": "Spider-Man: Across the Spider-Verse", "year": 2023, "rating": 4.5, "review": "Animation at its absolute peak."},
            {"title": "Mission: Impossible - Dead Reckoning", "year": 2023, "rating": 4.5, "review": "Non-stop thrills. The train sequence is insane!"},
            {"title": "Guardians of the Galaxy Vol. 3", "year": 2023, "rating": 4.0, "review": "A perfect send-off for the team. I cried."},
        ]
    },
    "Scary Sarah": {
        "username": "scarysarah",
        "email": "sarah@feedmovie.app",
        "bio": "Horror aficionado, loves a good scare",
        "recent_movies": [
            {"title": "Talk to Me", "year": 2023, "rating": 4.5, "review": "Fresh and terrifying. The hand scenes are nightmare fuel."},
            {"title": "Smile", "year": 2022, "rating": 4.0, "review": "That ending! I couldn't sleep for days."},
            {"title": "Barbarian", "year": 2022, "rating": 4.5, "review": "Go in blind. Trust me. Wild ride."},
            {"title": "Pearl", "year": 2022, "rating": 4.0, "review": "Mia Goth is absolutely unhinged. I loved it."},
            {"title": "Nope", "year": 2022, "rating": 4.0, "review": "Peele does spectacle horror like no one else."},
        ]
    },
    "Indie Ian": {
        "username": "indieian",
        "email": "ian@feedmovie.app",
        "bio": "Discovers hidden gems before they trend",
        "recent_movies": [
            {"title": "Aftersun", "year": 2022, "rating": 5.0, "review": "Devastating in the most beautiful way. That final shot..."},
            {"title": "The Worst Person in the World", "year": 2021, "rating": 4.5, "review": "A perfect portrait of millennial uncertainty."},
            {"title": "All of Us Strangers", "year": 2023, "rating": 4.5, "review": "Hauntingly tender. Andrew Scott is phenomenal."},
            {"title": "Saint Omer", "year": 2022, "rating": 4.0, "review": "Quietly powerful courtroom drama."},
            {"title": "Showing Up", "year": 2023, "rating": 4.0, "review": "Kelly Reichardt's gentle meditation on creativity."},
        ]
    },
    "Classic Clara": {
        "username": "classicclara",
        "email": "clara@feedmovie.app",
        "bio": "Old Hollywood expert, timeless taste",
        "recent_movies": [
            {"title": "Casablanca", "year": 1942, "rating": 5.0, "review": "The greatest love story ever told. Timeless."},
            {"title": "12 Angry Men", "year": 1957, "rating": 5.0, "review": "A masterclass in tension and character."},
            {"title": "Sunset Boulevard", "year": 1950, "rating": 5.0, "review": "Gloria Swanson IS Norma Desmond."},
            {"title": "Singin' in the Rain", "year": 1952, "rating": 4.5, "review": "Pure joy on screen. Gene Kelly was magic."},
            {"title": "Some Like It Hot", "year": 1959, "rating": 4.5, "review": "Nobody's perfect - and neither is any other comedy."},
        ]
    },
    "World Cinema Wes": {
        "username": "worldcinemawes",
        "email": "wes@feedmovie.app",
        "bio": "Explores films from every corner of the globe",
        "recent_movies": [
            {"title": "Parasite", "year": 2019, "rating": 5.0, "review": "Bong Joon-ho's masterpiece transcends language."},
            {"title": "City of God", "year": 2002, "rating": 5.0, "review": "Electrifying filmmaking from Brazil."},
            {"title": "Decision to Leave", "year": 2022, "rating": 4.5, "review": "Park Chan-wook at his most romantic and mysterious."},
            {"title": "RRR", "year": 2022, "rating": 4.5, "review": "Maximum cinema. The Naatu Naatu scene is legendary."},
            {"title": "Drive My Car", "year": 2021, "rating": 4.5, "review": "Three hours of pure contemplative beauty."},
        ]
    }
}


def ensure_curators_exist():
    """Create curator accounts and their activity if they don't exist."""
    init_database()

    created_count = 0

    for display_name, curator_data in CURATORS.items():
        username = curator_data["username"]

        # Check if curator already exists
        existing = get_user_by_username(username)
        if existing:
            continue

        print(f"Creating curator: {display_name} (@{username})...")

        # Create curator user account with a random password (they can't login)
        random_password = bcrypt.hashpw(os.urandom(32).hex().encode(), bcrypt.gensalt()).decode()
        user_id = create_user(
            email=curator_data["email"],
            password_hash=random_password,
            username=username
        )

        if not user_id:
            print(f"  ⚠️ Failed to create curator: {display_name}")
            continue

        # Update bio
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET bio = ? WHERE id = ?', (curator_data["bio"], user_id))
        conn.commit()
        conn.close()

        # Add their movie activity
        for movie_info in curator_data["recent_movies"]:
            title = movie_info["title"]
            year = movie_info["year"]

            # Get or create movie
            movie_data = tmdb_client.search_movie(title, year)
            if not movie_data:
                print(f"  ⚠️ Movie not found: {title}")
                continue

            movie = get_movie_by_tmdb_id(movie_data['tmdb_id'])
            if not movie:
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
            else:
                movie_id = movie['id']

            # Create activity
            action_type = 'reviewed' if movie_info.get('review') else 'rated'
            create_activity(
                user_id=user_id,
                action_type=action_type,
                movie_id=movie_id,
                rating=movie_info['rating'],
                review_text=movie_info.get('review')
            )

        print(f"  ✓ Created {display_name} with {len(curator_data['recent_movies'])} activities")
        created_count += 1

    if created_count > 0:
        print(f"\n✅ Created {created_count} curator accounts")

    return created_count


def get_curator_user_id(display_name: str) -> int:
    """Get the user ID for a curator by their display name."""
    if display_name not in CURATORS:
        return None

    username = CURATORS[display_name]["username"]
    user = get_user_by_username(username)
    return user['id'] if user else None


if __name__ == '__main__':
    ensure_curators_exist()
