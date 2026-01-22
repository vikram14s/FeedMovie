"""
Taste Profiles - Predefined movie taste profiles for quick onboarding.

Users select 1-2 profiles that match their taste, which helps bootstrap
recommendations before we have enough swipe data.
"""

from typing import Dict, List, Any

TASTE_PROFILES: Dict[str, Dict[str, Any]] = {
    "nolan_epic_fan": {
        "name": "Nolan Epic Fan",
        "icon": "🎬",
        "description": "Mind-bending sci-fi, complex narratives, IMAX-worthy spectacles",
        "representative_movies": [
            {"title": "Inception", "year": 2010},
            {"title": "Interstellar", "year": 2014},
            {"title": "Arrival", "year": 2016},
            {"title": "Blade Runner 2049", "year": 2017},
            {"title": "The Prestige", "year": 2006}
        ],
        "preferred_genres": ["Science Fiction", "Thriller", "Drama"],
        "preferred_themes": ["time manipulation", "dream", "space", "twist ending", "complex narrative"],
        "preferred_directors": ["Christopher Nolan", "Denis Villeneuve", "Alex Garland"],
        "avoid_themes": ["romantic comedy", "slapstick", "musical"],
        "prompt_boost": "Prioritize mind-bending sci-fi, complex narratives, and visually stunning films with deep themes."
    },

    "a24_indie_lover": {
        "name": "A24 Indie Lover",
        "icon": "🎭",
        "description": "Artistic vision, emotional depth, unconventional storytelling",
        "representative_movies": [
            {"title": "Everything Everywhere All at Once", "year": 2022},
            {"title": "Moonlight", "year": 2016},
            {"title": "The Lighthouse", "year": 2019},
            {"title": "Lady Bird", "year": 2017},
            {"title": "Hereditary", "year": 2018}
        ],
        "preferred_genres": ["Drama", "Horror", "Comedy"],
        "preferred_themes": ["coming of age", "family dynamics", "surreal", "atmospheric", "character study"],
        "preferred_studios": ["A24", "Neon", "Focus Features"],
        "avoid_themes": ["superhero", "franchise sequel", "CGI-heavy blockbuster"],
        "prompt_boost": "Prioritize indie films with artistic vision, character depth, and unconventional storytelling. A24-style films preferred."
    },

    "classic_hollywood": {
        "name": "Classic Hollywood",
        "icon": "🎞️",
        "description": "Golden age cinema, Hitchcock thrillers, timeless storytelling",
        "representative_movies": [
            {"title": "Casablanca", "year": 1942},
            {"title": "Vertigo", "year": 1958},
            {"title": "12 Angry Men", "year": 1957},
            {"title": "Sunset Boulevard", "year": 1950},
            {"title": "Rear Window", "year": 1954}
        ],
        "preferred_genres": ["Drama", "Thriller", "Romance", "Film Noir"],
        "preferred_decades": [1940, 1950, 1960, 1970],
        "preferred_directors": ["Alfred Hitchcock", "Billy Wilder", "Stanley Kubrick", "Orson Welles"],
        "avoid_themes": ["CGI effects", "franchise"],
        "prompt_boost": "Include classic films from the golden age of Hollywood. Prioritize timeless storytelling and masterful direction over modern spectacle."
    },

    "action_thrill_seeker": {
        "name": "Action Thrill Seeker",
        "icon": "💥",
        "description": "High-octane action, practical stunts, edge-of-seat tension",
        "representative_movies": [
            {"title": "Mad Max: Fury Road", "year": 2015},
            {"title": "John Wick", "year": 2014},
            {"title": "Top Gun: Maverick", "year": 2022},
            {"title": "Mission: Impossible - Fallout", "year": 2018},
            {"title": "The Raid", "year": 2011}
        ],
        "preferred_genres": ["Action", "Thriller", "Adventure"],
        "preferred_themes": ["heist", "revenge", "chase", "martial arts", "practical stunts"],
        "avoid_themes": ["slow burn", "dialogue heavy", "romance-focused"],
        "prompt_boost": "Prioritize high-octane action films with practical stunts, intense sequences, and adrenaline-pumping entertainment."
    },

    "horror_connoisseur": {
        "name": "Horror Connoisseur",
        "icon": "👻",
        "description": "Elevated horror, psychological terror, atmospheric dread",
        "representative_movies": [
            {"title": "The Shining", "year": 1980},
            {"title": "Get Out", "year": 2017},
            {"title": "Midsommar", "year": 2019},
            {"title": "The Witch", "year": 2015},
            {"title": "It Follows", "year": 2014}
        ],
        "preferred_genres": ["Horror", "Thriller", "Mystery"],
        "preferred_themes": ["psychological horror", "supernatural", "folk horror", "paranoia", "atmospheric"],
        "preferred_directors": ["Ari Aster", "Jordan Peele", "Robert Eggers", "Mike Flanagan"],
        "avoid_themes": ["jump scare heavy", "torture porn", "comedy horror"],
        "prompt_boost": "Prioritize elevated horror with psychological depth, atmospheric dread, and social commentary. Skip cheap jump scares."
    },

    "feel_good_comfort": {
        "name": "Feel-Good Comfort",
        "icon": "☀️",
        "description": "Heartwarming stories, witty dialogue, satisfying endings",
        "representative_movies": [
            {"title": "When Harry Met Sally", "year": 1989},
            {"title": "The Grand Budapest Hotel", "year": 2014},
            {"title": "Amélie", "year": 2001},
            {"title": "Paddington 2", "year": 2017},
            {"title": "Chef", "year": 2014}
        ],
        "preferred_genres": ["Comedy", "Romance", "Animation", "Drama"],
        "preferred_themes": ["found family", "underdog", "friendship", "redemption", "feel good"],
        "preferred_directors": ["Wes Anderson", "Nora Ephron", "Richard Curtis"],
        "avoid_themes": ["dark", "violence", "tragedy", "horror", "depressing ending"],
        "prompt_boost": "Prioritize heartwarming, feel-good films with satisfying endings. Comfort watching over challenging cinema."
    }
}


def get_all_profiles() -> List[Dict[str, Any]]:
    """
    Get all taste profiles for display.
    """
    profiles = []
    for profile_id, profile in TASTE_PROFILES.items():
        profiles.append({
            "id": profile_id,
            "name": profile["name"],
            "icon": profile["icon"],
            "description": profile["description"],
            "representative_movies": profile["representative_movies"]
        })
    return profiles


def get_profile(profile_id: str) -> Dict[str, Any]:
    """
    Get a specific taste profile by ID.
    """
    return TASTE_PROFILES.get(profile_id)


def build_profile_prompt_context(profile_ids: List[str]) -> str:
    """
    Build prompt context from selected taste profiles.

    Returns a string to inject into AI prompts.
    """
    if not profile_ids:
        return ""

    lines = ["### SELECTED TASTE PROFILES"]

    for pid in profile_ids:
        profile = TASTE_PROFILES.get(pid)
        if not profile:
            continue

        lines.append(f"\n**{profile['name']}** ({profile['icon']})")
        lines.append(f"Style: {profile['description']}")

        if profile.get('preferred_genres'):
            lines.append(f"Preferred genres: {', '.join(profile['preferred_genres'])}")

        if profile.get('preferred_themes'):
            lines.append(f"Preferred themes: {', '.join(profile['preferred_themes'][:5])}")

        if profile.get('preferred_directors'):
            lines.append(f"Favorite directors: {', '.join(profile['preferred_directors'][:3])}")

        if profile.get('avoid_themes'):
            lines.append(f"AVOID: {', '.join(profile['avoid_themes'])}")

        if profile.get('prompt_boost'):
            lines.append(f"\n→ {profile['prompt_boost']}")

    return '\n'.join(lines)


if __name__ == '__main__':
    print("Available Taste Profiles:\n")
    for profile in get_all_profiles():
        print(f"{profile['icon']} {profile['name']}")
        print(f"   {profile['description']}")
        movies = ', '.join([m['title'] for m in profile['representative_movies']])
        print(f"   Representative: {movies}")
        print()

    print("\n" + "=" * 60)
    print("Example prompt context for 'nolan_epic_fan' + 'a24_indie_lover':")
    print("=" * 60)
    print(build_profile_prompt_context(['nolan_epic_fan', 'a24_indie_lover']))
