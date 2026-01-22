"""
Populate onboarding_movies table with curated popular films for swipe onboarding.

These are well-known, recognizable movies spanning different genres and eras.
"""

from database import add_onboarding_movie, get_onboarding_movies_count, init_database
from tmdb_client import get_movie_details, search_movie

# Curated list of popular, recognizable movies for onboarding
# Mix of genres, eras, and styles - movies most people have heard of
ONBOARDING_MOVIES = [
    # Modern Blockbusters
    {"title": "Inception", "year": 2010},
    {"title": "The Dark Knight", "year": 2008},
    {"title": "Interstellar", "year": 2014},
    {"title": "Parasite", "year": 2019},
    {"title": "Everything Everywhere All at Once", "year": 2022},
    {"title": "Oppenheimer", "year": 2023},
    {"title": "Dune", "year": 2021},
    {"title": "Spider-Man: Into the Spider-Verse", "year": 2018},
    {"title": "Mad Max: Fury Road", "year": 2015},
    {"title": "Get Out", "year": 2017},

    # Classic Favorites
    {"title": "The Shawshank Redemption", "year": 1994},
    {"title": "Pulp Fiction", "year": 1994},
    {"title": "Fight Club", "year": 1999},
    {"title": "The Matrix", "year": 1999},
    {"title": "Forrest Gump", "year": 1994},
    {"title": "Goodfellas", "year": 1990},
    {"title": "The Godfather", "year": 1972},
    {"title": "Schindler's List", "year": 1993},
    {"title": "The Silence of the Lambs", "year": 1991},
    {"title": "Titanic", "year": 1997},

    # Comedies
    {"title": "The Grand Budapest Hotel", "year": 2014},
    {"title": "Superbad", "year": 2007},
    {"title": "The Big Lebowski", "year": 1998},
    {"title": "Bridesmaids", "year": 2011},
    {"title": "Knives Out", "year": 2019},

    # Action/Adventure
    {"title": "John Wick", "year": 2014},
    {"title": "Top Gun: Maverick", "year": 2022},
    {"title": "The Avengers", "year": 2012},
    {"title": "Gladiator", "year": 2000},
    {"title": "Kill Bill: Vol. 1", "year": 2003},

    # Horror/Thriller
    {"title": "A Quiet Place", "year": 2018},
    {"title": "Hereditary", "year": 2018},
    {"title": "The Shining", "year": 1980},
    {"title": "Se7en", "year": 1995},
    {"title": "Midsommar", "year": 2019},

    # Sci-Fi
    {"title": "Arrival", "year": 2016},
    {"title": "Blade Runner 2049", "year": 2017},
    {"title": "Ex Machina", "year": 2014},
    {"title": "Her", "year": 2013},
    {"title": "Alien", "year": 1979},

    # Drama
    {"title": "Whiplash", "year": 2014},
    {"title": "La La Land", "year": 2016},
    {"title": "The Social Network", "year": 2010},
    {"title": "Moonlight", "year": 2016},
    {"title": "12 Years a Slave", "year": 2013},

    # Animation
    {"title": "Spirited Away", "year": 2001},
    {"title": "WALL-E", "year": 2008},
    {"title": "Coco", "year": 2017},
    {"title": "Your Name", "year": 2016},
    {"title": "The Lion King", "year": 1994},
]


def populate_onboarding_movies():
    """Populate the onboarding_movies table."""
    # Initialize database first
    init_database()

    current_count = get_onboarding_movies_count()
    if current_count >= 50:
        print(f"Onboarding movies already populated ({current_count} movies)")
        return

    print(f"Populating onboarding movies (currently {current_count})...")

    for i, movie_info in enumerate(ONBOARDING_MOVIES, 1):
        title = movie_info["title"]
        year = movie_info["year"]

        print(f"[{i}/{len(ONBOARDING_MOVIES)}] Fetching {title} ({year})...")

        # Search TMDB for movie
        movie_data = search_movie(title, year)

        if movie_data:
            add_onboarding_movie(
                tmdb_id=movie_data['tmdb_id'],
                title=movie_data['title'],
                year=movie_data['year'],
                poster_path=movie_data.get('poster_path'),
                genres=movie_data.get('genres', []),
                popularity_rank=i
            )
            print(f"   ✓ Added: {movie_data['title']}")
        else:
            print(f"   ⚠️ Not found on TMDB: {title}")

    final_count = get_onboarding_movies_count()
    print(f"\n✅ Onboarding movies populated: {final_count} movies")


if __name__ == '__main__':
    populate_onboarding_movies()
